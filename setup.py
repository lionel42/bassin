from distutils.core import setup
setup(
  name = 'bassin',
  packages = ['bassin'],
  version = '0.2',
  license='MIT',
  description = (
      'Python optimization script used for optimizing water flow out of '
      'a catch basin or a dam.'
  ),
  url = 'https://github.com/lionel42/bassin',
  download_url = 'https://github.com/lionel42/bassin/archive/refs/tags/v_0.2.tar.gz',
  keywords = ['bassin', 'basin', 'dam', 'pumping', 'flow', 'optimization'],
  install_requires=[
          'numpy',
          'matplotlib',
      ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Intended Audience :: Science/Research',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3',
    'Programming Language :: Python :: 3.9',
  ],
)