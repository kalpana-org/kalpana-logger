kalpana-logger
==============

Logs how much and when you write.

Use the command `l` to start logging a file, with argument `y` to use the current (saved) wordcount as an offset (those words wont show up in the statistics) or `n` to not use an offset.

As of now, this plugin pretty much depends on Dropbox or some equally syncing program. The `rootdir` variable in the config should point to the main Dropbox directory, and the `logdir` variable should point to the directory where you want the logfiles to be placed, *relative* to the `rootdir`.
