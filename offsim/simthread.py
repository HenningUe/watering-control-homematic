
# encoding: utf-8

_all_sim_threads_to_be_waited_for = list()


def wait_till_all_threads_are_finished(reraise_thread_exception=False):
    import bewaesserung
    bewaesserung.ThreadContainer.wait_till_all_threads_are_finished(reraise_thread_exception)
