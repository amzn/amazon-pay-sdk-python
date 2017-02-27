from setuptools import setup
import amazon_pay.version as pwa_version

setup(
    name='amazon_pay',
    packages=['amazon_pay'],
    version=pwa_version.versions['application_version'],
    description='Amazon Pay Python SDK',
    url='https://github.com/amzn/amazon-pay-sdk-python',
    download_url='https://github.com/amzn/amazon-pay-sdk-python/tarball/{}'.format(
        pwa_version.versions['application_version']),
    author='EPS-DSE',
    author_email='amazon-pay-sdk@amazon.com',
    license='Apache License version 2.0, January 2004',
    install_requires=['pyOpenSSL >= 0.11',
                      'requests >= 2.6.0'],
    keywords=['Amazon', 'Payments', 'Login', 'Python', 'API', 'SDK'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.4',
        'Topic :: Software Development :: Libraries',
        'Topic :: Software Development :: Libraries :: Python Modules']
)
