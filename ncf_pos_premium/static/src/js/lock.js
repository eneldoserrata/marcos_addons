odoo.define('ncf_pos_premium.pos_lock_screen', function (require) {
    "use strict";
    var chrome = require('point_of_sale.chrome');
    var core = require('web.core');
    var PosBaseWidget = require('point_of_sale.BaseWidget');
    var gui = require('point_of_sale.gui');
    var screens = require('point_of_sale.screens');
    var _t = core._t;

    chrome.Chrome.include({
        build_widgets: function () {
            var self = this;
            this._super();
            $(".lock-screen-ev").click(function () {
                self.gui.show_popup('lock_screen');
            });
        },
    });

    var LockscreenWidget = PosBaseWidget.extend({
        template: 'LockscreenWidget',

        renderElement: function () {
            var self = this;
            this._super();
        },
        unlock_user: function (options) {
            options = options || {};
            var self = this;
            var def = new $.Deferred();

            var list = [];
            for (var i = 0; i < this.pos.users.length; i++) {
                var user = this.pos.users[i];
                if (!options.only_managers || user.role === 'manager') {
                    list.push({
                        'label': user.name,
                        'item': user,
                    });
                }
            }

            this.gui.show_popup('selection', {
                'title': options.title || _t('Select User'),
                list: list,
                confirm: function (user) {
                    def.resolve(user);
                },
                cancel: function () {
                    self.gui.show_popup('lock_screen');
                },
            });

            return def.then(function (user) {
                if (options.security && user !== options.current_user && user.pos_security_pin) {
                    return self.unlock_ask_password(user.pos_security_pin).then(function () {
                        return user;
                    });
                } else {
                    return user;
                }
            });
        },
        unlock_ask_password: function (password) {
            var self = this;
            var ret = new $.Deferred();
            if (password) {
                this.gui.show_popup('password', {
                    'title': _t('Password ?'),
                    'not_close': true,
                    confirm: function (pw) {
                        if (pw !== password) {
                            self.gui.show_popup('error', _t('Incorrect Password'));
                            ret.reject();
                        } else {
                            ret.resolve();
                        }
                    },
                });
            } else {
                ret.resolve();
            }
            return ret;
        },
        show: function () {
            var self = this;
            this._super();
            $(".lock_widget").click(function () {
                self.unlock_user({
                    'security': true,
                    'current_user': self.pos.get_cashier(),
                    'title': _t('Seleccione el vendedor')
                })

            });
        },

        close: function () {
        }

    });

    gui.define_popup({
        'name': 'lock_screen',
        'widget': LockscreenWidget,
    });
});

