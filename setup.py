from setuptools import setup

setup(name="slocky",
      version="0.0.0",
      description="Simple server-client commuication framework build ontop of TLS.",
      long_description=open("README"),
      url="https://github.com/Aeva/slocky",
      author="Aeva Palecek",
      author_email="aeva.ntsc@gmail.com",
      license="GPLv3",
      packages=["slocky"],
      zip_safe=False,
      test_suite="nose.collector",
      install_requires=[
        ],
      tests_require=[
          "nose",
          ])
