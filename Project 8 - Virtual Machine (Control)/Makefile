###############################################################################
#
# Makefile for a script (e.g. Python), project 8
#
###############################################################################

# We want our users to have a simple API to run the Assembler, no matter the language
# it was written in. So, we need a "wrapper" that will hide all language-specific details to do so,
# thus enabling our users to simply type 'Assembler <path>' in order to use it.
# This is a sample makefile. 
# The purpose of makefiles is to make sure that after running "make" your project is ready for execution.
# Usually, scripting language (e.g. Python) based projects only need execution permissions for your run 
# file executable to run. The executable for project 6 should be called Assembler.
# Obviously, your project may be more complicated and require a different makefile.
# For this file (Makefile-script) to run when you call "make", rename it to "Makefile".

# The following line is a rule declaration. A makefile rule is a list of prerequisites (other rules that 
# need to be run before this rule) and commands that are run one after the other. The "all" rule is what 
# runs when you call "make":
all:
	chmod a+x VMtranslator

# As you can see, all it does is grant execution permissions for your run time executable, so your project 
# will be able to run on the graders' computers. In this case, the "all" rule has no preqrequisites.

# A general rule looks like this:
# rule_name: prerequisite1 prerequisite2 prerequisite3 prerequisite4 ...
#	command1
#	command2
#	command3
#	...
# Where each preqrequisite is a rule name, and each command is a command-line command (for example chmod, 
# javac, echo, etc').