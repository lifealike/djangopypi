from contextlib import contextmanager
import os
import shutil
import tempfile

from django.core.management.base import CommandError
from pip.exceptions import DistributionNotFound
from pip.index import PackageFinder
from pip.req import InstallRequirement, RequirementSet

from djangopypi.management.commands.ppadd import Command as BasicCommand


@contextmanager
def tempdir():
    """Simple context that provides a temporary directory that is deleted
    when the context is exited.
    """
    d = tempfile.mkdtemp(".tmp", "djangopypi.")
    try:
        yield d
    finally:
        shutil.rmtree(d)


def pip_install(name, tmpdir):
    build_dir = os.path.join(tmpdir, 'build')
    src_dir = os.path.join(tmpdir, 'src')
    download_dir = os.path.join(tmpdir, 'download')

    os.mkdir(build_dir)
    os.mkdir(src_dir)
    os.mkdir(download_dir)

    finder = PackageFinder(
        find_links=[],
        index_urls=['https://pypi.python.org/simple/'],
        use_mirrors=False,
        allow_all_external=True,
        allow_all_insecure=True,
    )

    requirement_set = RequirementSet(
        build_dir=build_dir,
        src_dir=src_dir,
        download_dir=download_dir,
        ignore_installed=True,
        ignore_dependencies=True
    )
    requirement_set.add_requirement(InstallRequirement.from_line(name, None))
    requirement_set.prepare_files(finder)

    # should be exactly one
    filename = os.listdir(download_dir)[0]
    path = os.path.join(download_dir, filename)
    return path


class Command(BasicCommand):
    """Download package from pypi.python.org and add to index"""
    def handle_label(self, label, **options):
        with tempdir() as tmp:
            try:
                path = pip_install(label, tmp)
                self._save_package(path, options['owner'])
            except DistributionNotFound as ex:
                raise CommandError(ex)
