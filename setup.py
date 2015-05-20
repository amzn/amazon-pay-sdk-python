from setuptools import setup
import pay_with_amazon.version as pwa_version

setup(
    name='pay_with_amazon',
    packages=['pay_with_amazon'],
    version=pwa_version.versions['application_version'],
    description='Login and Pay with Amazon Python SDK',
    url='https://github.com/amzn/login-and-pay-with-amazon-sdk-python',
    download_url='https://github.com/amzn/login-and-pay-with-amazon-sdk-python/tarball/{}'.format(
        pwa_version.versions['application_version']),
    author='EPS-DSE',
    author_email='pay-with-amazon-sdk@amazon.com',
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
