from distutils.core import setup

# todo: add install of udev file
#       leave note to add users to 'dialout' or whatever group can use TTYs

setup(
	name='vanscreen', 
	version="0.1", 
	description="Collect magnetic stray field and dipole moments from small parts",
	author="C. Dorman",
	author_email="cole-dorman@uiwo.edu",
	url="https://research-git.uiowa.edu/space-physics/tracers/magic/utilities",
	install_requires=[
		'numpy', 'tldevice', 'scipy', 'matplotlib'
	],
	scripts=['scripts/mag_screen','scripts/mag_screen_gui'],
	py_modules=['vanscreen']
)
