from setuptools import setup, find_packages
import vmware_exporter

setup(
    name='vmware_exporter',
    version=vmware_exporter.__version__,
    author=vmware_exporter.__author__,
    description='VMWare VCenter Exporter for Prometheus',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/muravsky/vmware_exporter',
    project_urls={
        'Upstream': vmware_exporter.__upstream_url__,
        'Original project': 'https://github.com/rverchere/vmware_exporter',
    },
    download_url=('https://github.com/muravsky/vmware_exporter/archive/refs/tags/v%s.tar.gz' %
                  vmware_exporter.__version__),
    keywords=['VMWare', 'VCenter', 'Prometheus'],
    license=vmware_exporter.__license__,
    packages=find_packages(exclude=['*.test', '*.test.*']),
    include_package_data=True,
    install_requires=open('requirements.txt').readlines(),
    entry_points={
        'console_scripts': [
            'vmware_exporter=vmware_exporter.vmware_exporter:main'
        ]
    }
)
