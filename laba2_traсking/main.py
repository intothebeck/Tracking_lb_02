import threading
from pynput import keyboard
from rx.subject import Subject
from rx import operators as ops

# Создаем Subject для передачи событий
class KeyboardTracker:
    def __init__(self):
        self.subject = Subject()
        self._running = True
        self.pressed_keys = set()  # Для отслеживания комбинаций клавиш

    def start_tracking(self):
        def on_press(key):
            try:
                if key not in self.pressed_keys:
                    self.pressed_keys.add(key)
                    self.subject.on_next(f"Key pressed: {key.char}")
                    if (keyboard.Key.ctrl_l in self.pressed_keys or keyboard.Key.ctrl_r in self.pressed_keys) \
                            and key == keyboard.KeyCode.from_char('x'):
                        self.subject.on_completed()
                        self._running = False
            except AttributeError:
                if key not in self.pressed_keys:
                    self.pressed_keys.add(key)
                    self.subject.on_next(f"Special key pressed: {key}")

        def on_release(key):
            self.subject.on_next(f"Key released: {key}")
            if key in self.pressed_keys:
                self.pressed_keys.remove(key)

        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()

    def stop_tracking(self):
        self._running = False

# Подписчик, который записывает события в файл
class FileSubscriber:
    def __init__(self, filename):
        self.filename = filename

    def write_to_file(self, event):
        try:
            with open(self.filename, 'a') as file:
                file.write(event + '\n')
                file.flush()
        except Exception as e:
            print(f"Error writing to file: {e}")

# Функция для запуска трекера в отдельном потоке
def start_tracker_in_thread(tracker):
    tracker_thread = threading.Thread(target=tracker.start_tracking)
    tracker_thread.daemon = True
    tracker_thread.start()
    return tracker_thread


if __name__ == "__main__":
    tracker = KeyboardTracker()
    subscriber = FileSubscriber("keyboard_events.log")

    # Подписка на события
    tracker.subject.pipe(
        ops.do_action(on_next=subscriber.write_to_file,
                      on_error=lambda e: print(f"Error: {e}"),
                      on_completed=lambda: print("Tracking completed."))
    ).subscribe(
        on_next=lambda event: print(event),
        on_error=lambda e: print(f"Tracker error: {e}"),
        on_completed=lambda: print("All subscribers completed.")
    )

    thread = start_tracker_in_thread(tracker)

    try:
        thread.join()
    except KeyboardInterrupt:
        tracker.stop_tracking()
        print("Tracker stopped by user.")
