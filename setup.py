from setuptools import setup, find_packages
 
setup(
    name='django-friends',
    version='0.1.0',
    description='friendship, contact and invitation management for the Django web framework',
    author='James Tauber',
    author_email='jtauber@jtauber.com',
    url='http://code.google.com/p/django-friends/',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Framework :: Django',
    ],
    include_package_data=True,
    zip_safe=False,
    install_requires=['setuptools'],
)
