project ('lollypop-po')

if not meson.is_subproject()
    message('WARNING: This project is only intended to be used as a subproject!')
endif

i18n = import('i18n')


message('Update translations')
i18n.gettext('lollypop', preset: 'glib')
