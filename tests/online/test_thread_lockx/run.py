
import threading
import time

import lockx
import msgs

tlock = lockx.RLockTraceable()


def func1():
    func2()


func1._unique_name = "Func1"


def func1a():
    func2()


func1a._unique_name = "Func1a"


def func1b():
    func2()


func1b._unique_name = "Func1b"


def func2():
    func12()


def func12():
    with tlock:
        func22()


def func22():
    time.sleep(2.0)


if __name__ == "__main__":
    print("Start Lock logging")
    lockx.ThreadContainer.run_threaded_deco(func1)()
    lockx.ThreadContainer.run_threaded_deco(func1a)()
    lockx.ThreadContainer.run_threaded_deco(func1b)()

    while True:
        if lockx.ThreadContainer.any_thread_is_alive():
            time.sleep(0.2)
            continue
        break

#     for msg in msgs.msgs:
#         print(msg)
    print("Finished")

