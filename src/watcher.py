import os
import asyncio
import errno

import logging as log


class FileWatcher(object):
    def __init__(self, path, event, interval, notify_on_appearance=False):
        self.path = path
        self.event = event
        self.last_modification_time = None
        self.interval = interval
        self.notify_on_appearance = notify_on_appearance
        self.task = asyncio.create_task(self._watcher())

    async def _watcher(self):
        while True:
            try:
                stat = os.stat(self.path)
            except FileNotFoundError:
                if self.notify_on_appearance and self.last_modification_time is not None:
                    self.last_modification_time = None
                    self.event.set()
            except OSError as e:
                if e.errno != errno.EACCES and getattr(e, 'winerror', None) != 5:
                    log.exception(f'Stating {self.path} has failed: {str(e)}')
            except Exception as e:
                log.exception(f'Stating {self.path} has failed: {str(e)}')
            else:
                if self.last_modification_time is None:
                    self.last_modification_time = stat.st_mtime
                    if self.notify_on_appearance:
                        self.event.set()
                elif stat.st_mtime != self.last_modification_time:
                    self.last_modification_time = stat.st_mtime
                    if not self.event.is_set():
                        self.event.set()
            finally:
                await asyncio.sleep(self.interval)
