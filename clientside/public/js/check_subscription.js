$(document).ready(function() {
    $( ".sticky-top" ).click(function() {
        if (frappe.boot.subscription_expired) {
            if (!window.location.pathname.startsWith('/app/subscription-info')) {
                var userRoles = frappe.user_roles;
                if (userRoles.includes('OneHash Manager')){
                    let dialog = new frappe.ui.Dialog({
                        title: __('Subscription Expired'),
                        indicator: 'red',
                        static: true, 
                        no_close: true,
                        fields: [
                            {
                                fieldtype: 'HTML',
                                options: '<p>Your subscription has expired. Please renew your plan to continue using the platform.</p>'
                            }
                        ],
                        primary_action_label: __('Go to Subscription Page'),
                        primary_action() {
                            window.location.href = '/app/subscription-info';
                        }
                    });
        
                    dialog.show();
                } else {
                    let dialog = new frappe.ui.Dialog({
                        title: __('Subscription Expired'),
                        indicator: 'red',
                        static: true, 
                        no_close: true,
                        fields: [
                            {
                                fieldtype: 'HTML',
                                options: '<p>Your subscription has expired. Please ask your administrator to renew your plan to continue using the platform.</p>'
                            }
                        ],
                    });
        
                    dialog.show();
                }
            }
        }
    });
    $( ".main-section" ).on('click', function(event) {
        if (frappe.boot.subscription_expired) {
            if (!window.location.pathname.startsWith('/app/subscription-info')) {
                var userRoles = frappe.user_roles;
                if (userRoles.includes('OneHash Manager')){
                    let dialog = new frappe.ui.Dialog({
                        title: __('Subscription Expired'),
                        indicator: 'red',
                        static: true, 
                        no_close: true,
                        fields: [
                            {
                                fieldtype: 'HTML',
                                options: '<p>Your subscription has expired. Please renew your plan to continue using the platform.</p>'
                            }
                        ],
                        primary_action_label: __('Go to Subscription Page'),
                        primary_action() {
                            window.location.href = '/app/subscription-info';
                        }
                    });
        
                    dialog.show();
                } else {
                    let dialog = new frappe.ui.Dialog({
                        title: __('Subscription Expired'),
                        indicator: 'red',
                        static: true, 
                        no_close: true,
                        fields: [
                            {
                                fieldtype: 'HTML',
                                options: '<p>Your subscription has expired. Please ask your administrator to renew your plan to continue using the platform.</p>'
                            }
                        ],
                    });
        
                    dialog.show();
                }
            }
        }
    });
    $( "#body" ).click(function() {
        if (frappe.boot.subscription_expired) {
            if (!window.location.pathname.startsWith('/app/subscription-info')) {
                var userRoles = frappe.user_roles;
                if (userRoles.includes('OneHash Manager')){
                    let dialog = new frappe.ui.Dialog({
                        title: __('Subscription Expired'),
                        indicator: 'red',
                        static: true, 
                        no_close: true,
                        fields: [
                            {
                                fieldtype: 'HTML',
                                options: '<p>Your subscription has expired. Please renew your plan to continue using the platform.</p>'
                            }
                        ],
                        primary_action_label: __('Go to Subscription Page'),
                        primary_action() {
                            window.location.href = '/app/subscription-info';
                        }
                    });
        
                    dialog.show();
                } else {
                    let dialog = new frappe.ui.Dialog({
                        title: __('Subscription Expired'),
                        indicator: 'red',
                        static: true, 
                        no_close: true,
                        fields: [
                            {
                                fieldtype: 'HTML',
                                options: '<p>Your subscription has expired. Please ask your administrator to renew your plan to continue using the platform.</p>'
                            }
                        ],
                    });
        
                    dialog.show();
                }
            }
        }
    });
});