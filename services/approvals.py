"""Approval service helpers — thin wrappers around authz."""

import authz


def can_approve(db, user_id, rol, approval):
    """Return True if the user may act on the given approval step."""
    return authz.can_act_on_approval(db, user_id, rol, approval)


def approval_error(db, user_id, rol, approval):
    """Return a Turkish error message if action is blocked, else None."""
    return authz.approval_action_error(db, user_id, rol, approval)
