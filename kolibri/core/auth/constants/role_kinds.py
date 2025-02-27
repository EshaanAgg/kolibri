"""
This module contains constants representing the kinds of "roles" that a user can have with respect to a Collection.
"""


ADMIN = "admin"
COACH = "coach"
ASSIGNABLE_COACH = "classroom assignable coach"

choices = (
    (ADMIN, "Admin"),
    (COACH, "Coach"),
    (ASSIGNABLE_COACH, "Classroom Assignable Coach"),
)
