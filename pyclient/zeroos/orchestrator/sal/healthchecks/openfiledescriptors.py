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
    result['category'] = 'System'
    result['message'] = 'Open file descriptors for all processes are within limit'

    for process in node.client.process.list():
        for rlimit in process['rlimit']:
            if rlimit['resource'] == psutil.RLIMIT_NOFILE:
                if (0.9 * rlimit['hard']) > process['ofd'] >= (0.9 * rlimit['soft']):
                    result['status'] = 'WARNING'
                    result['message'] = 'Ofd for process %%s exceeded 90\% of the soft limit' % process['pid']
                    results.append(result)
                elif process['ofd'] >= (0.9 * rlimit['hard']):
                    result['status'] = 'ERROR'
                    result['message'] = 'Ofd for process %%s exceeded 90\% of the hard limit' % process['pid']
                    results.append(result)
                break

    return results if results else [result]


if __name__ == '__main__':
    action()
