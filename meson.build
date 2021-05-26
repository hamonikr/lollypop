project('lollypop',
  version: '1.4.19',
  meson_version: '>= 0.46.0'
)
revision = run_command('bin/revision.sh').stdout().strip()
if revision == ''
  revision=meson.project_version()
endif

if get_option('devel').enabled()
  appid='None'
else
  appid='org.gnome.Lollypop'
endif

i18n = import('i18n')
py_mod = import('python')
project_id = 'org.gnome.Lollypop'

message('Looking for dependencies')
py_installation = py_mod.find_installation('python3')
if not py_installation.found()
    error('No valid python3 binary found')
else
    message('Found python3 binary')
endif

# Dependencies
dependency('gobject-introspection-1.0', version: '>= 1.35.0')
dependency('gtk+-3.0', version: '>= 3.22')
dependency('libsoup-2.4')
dependency('glib-2.0')
dependency('pygobject-3.0', version: '>= 3.29.1')

python_dir = join_paths(get_option('prefix'), py_installation.get_install_dir())
LIBEXEC_DIR = join_paths(get_option('prefix'), get_option('libexecdir'))
DATA_DIR = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
bindir = join_paths(get_option('prefix'), get_option('bindir'))

conf = configuration_data()
conf.set('PACKAGE_URL', 'https://wiki.gnome.org/Apps/Lollypop')
conf.set('DATA_DIR', DATA_DIR)
conf.set('LOCALE_DIR', join_paths(get_option('prefix'), get_option('datadir'), 'locale'))
conf.set('PYTHON_DIR', python_dir)
#conf.set('PYTHON_EXEC_DIR', join_paths(get_option('prefix'), py_installation.get_path('stdlib')))
conf.set('libexecdir', LIBEXEC_DIR)
conf.set('VERSION', meson.project_version())
conf.set('REVISION', revision)
conf.set('APPID', appid)

subdir('data')
subproject('po')
subdir('search-provider')

install_subdir(
  'lollypop',
  install_dir: python_dir
)

#install_subdir(
#  'thirdparty',
#  install_dir: join_paths(python_dir, 'lollypop')
#)

message('Preparing init file')
configure_file(
  input: 'lollypop.in',
  output: 'lollypop',
  configuration: conf,
  install_dir: bindir
)

meson.add_install_script('meson_post_install.py')
