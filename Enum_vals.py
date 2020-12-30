"""
Enums are names bound to unique, constant values.
Unlike a list, enums are immutable, so the programmer gets warned 
that they can't do illegal actions such as editing the value, or incorrect capitalisation
"""

import enum

class Section(enum.Enum):
   """Choose the section type, SHS, RHS or CHS"""
   SHS = enum.auto()
   RHS = enum.auto()
   CHS = enum.auto()

class Member(enum.Enum):
   """Choose the member type, CHORD OR BRACE"""
   CHORD = enum.auto()
   BRACE = enum.auto()

class Code(enum.Enum):
   """Choose the code for loading section databases, AS (Australia), EN (Europe)"""
   AS = enum.auto()
   EN = enum.auto()