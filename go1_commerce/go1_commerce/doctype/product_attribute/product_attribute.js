frappe.ui.form.on('Product Attribute', {
    refresh: function(frm) {
        if (frappe.user.has_role('System Manager') || frappe.user.has_role('Admin') || frappe.user.has_role('Super Admin')) {
            return false
        }
    }

});