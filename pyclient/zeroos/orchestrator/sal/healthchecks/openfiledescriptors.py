import psutil


descr = """
Check open file descriptors for each node process, if it exceeds 90% of the soft limit, it raises a warning,
if it exceeds 90% of the hard limit, it raises an error.
"""


def action(node):
    results = list()
    result = dict()
    result['id'] = 'OPENFILEDESCRIPTORS'
    result['name'] = 'OPENFILEDESCRIPTORS'
    result['status'] = 'OK'
    result['resource'] = 'System Load'
    result['category'] = 'System Load'
    result['message'] = 'Open file descriptors for all processes are within limit'

    for process in node.client.process.list():
        for rlimit in process['rlimit']:
            if rlimit['resource'] == psutil.RLIMIT_NOFILE:
                pid = process['pid']
                if (0.9 * rlimit['soft']) <= process['ofd'] < (0.9 * rlimit['hard']):
                    result['status'] = 'WARNING'
                    result['message'] = 'Open file descriptors for process %s exceeded 90%% of the soft limit' % pid
                    results.append(result)
                elif process['ofd'] >= (0.9 * rlimit['hard']):
                    result['status'] = 'ERROR'
                    result['message'] = 'Open file descriptors for process %s exceeded 90%% of the hard limit' % pid
                    results.append(result)
                break

    return results if results else [result]


if __name__ == '__main__':
    action()
