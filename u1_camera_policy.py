RESET_WINDOW = 90.0


def should_restart_monitor(stale_for):
    return stale_for >= RESET_WINDOW


def should_release_lan_on_wan_stop(domain):
    return domain == "wan"


def is_wan_stop_log_line(line):
    return (
        "[CAMSRV:232] Stop camera monitor, domain is wan"
        in line
    )


def should_reopen_log(open_inode, current_inode):
    if open_inode is None:
        return True
    return open_inode != current_inode


WAN_RECOVERY_FALLBACK = 600.0


def should_restart_during_wan_recovery(recovery_for):
    return recovery_for >= WAN_RECOVERY_FALLBACK


def is_wan_start_log_line(line):
    return (
        "[CAMSRV:164] Start camera monitor, domain is wan"
        in line
    )



WAN_FAILURE_THRESHOLD = 15.0


def is_failed_wan_session(duration):
    return duration < WAN_FAILURE_THRESHOLD


def next_wan_start_time(recovery_active, current_start, new_start):
    if recovery_active and current_start is not None:
        return current_start
    return new_start
