
function click_events(e) {
  let order_id = $(e).attr('data-id');
  if($(e).attr('checked')){
    $(e).removeAttr('checked')
    for( var i = 0; i < cur_frm.selected_order_list.length; i++){ 
      if ( cur_frm.selected_order_list[i] ===order_id) {
        cur_frm.selected_order_list.splice(i, 1); 
      }
   }
   
  }
  else{    
    $(e).attr('checked','checked')
    let order_detail = order_id;
    if (order_detail) {
        cur_frm.selected_order_list.push(order_detail)
    }
  }
  
}

frappe.ui.form.Form.prototype.savecancel = function(btn, callback, on_error) {
  console.log("---savecancel---")
    const me = this;
    frappe.call({
        method: "go1_commerce.accounts.defaults.get_submitted_linked_docs",
        args: {
            doctype: me.doc.doctype,
            name: me.doc.name
        },
        freeze: true,
        callback: (r) => {
          console.log(r)
            if (!r.exc && r.message.count > 0) {
                me._cancel_all(r, btn, callback, on_error);
            } else {
                me._cancel(btn, callback, on_error, false);
            }
        }
    });
}

    frappe.ui.form.Form.prototype._cancel = function(btn, callback, on_error, skip_confirm) {
      console.log("---cancel--")
        const me = this;
        const cancel_doc = () => {
            frappe.validated = true;
            me.script_manager.trigger("before_cancel").then(() => {
                if (!frappe.validated) {
                    return me.handle_save_fail(btn, on_error);
                }

                var after_cancel = function(r) {
                    if (r.exc) {
                        me.handle_save_fail(btn, on_error);
                    } else {
                        frappe.utils.play_sound("cancel");
                        me.refresh();
                        callback && callback();
                        me.script_manager.trigger("after_cancel");
                    }
                };
                frappe.ui.form.save(me, "cancel", after_cancel, btn);
            });
        }

        if (skip_confirm) {
            cancel_doc();
        } else {
            frappe.confirm(__("Permanently Cancel {0}?", [this.docname]), cancel_doc, me.handle_save_fail(btn, on_error));
        }
    }

frappe.ui.form.Form.prototype._cancel_all = function(r, btn, callback, on_error) {
    const me = this;
    let links_text = "";
    let links = r.message.docs;
    const doctypes = Array.from(new Set(links.map(link => link.doctype)));

    for (let doctype of doctypes) {
        let docnames = links
            .filter((link) => link.doctype == doctype)
            .map((link) => frappe.utils.get_form_link(link.doctype, link.name, true))
            .join(", ");
        links_text += `<li><strong>${doctype}</strong>: ${docnames}</li>`;
    }
    links_text = `<ul>${links_text}</ul>`;

    let confirm_message = __('{0} {1} is linked with the following submitted documents: {2}',
        [(me.doc.doctype).bold(), me.doc.name, links_text]);

    let can_cancel = links.every((link) => frappe.model.can_cancel(link.doctype));
    if (can_cancel) {
        confirm_message += __('Do you want to cancel all linked documents?');
    } else {
        confirm_message += __('You do not have permissions to cancel all linked documents.');
    }

    let d = new frappe.ui.Dialog({
        title: __("Cancel All Documents"),
        fields: [{
            fieldtype: "HTML",
            options: `<p class="frappe-confirm-message">${confirm_message}</p>`
        }]
    }, () => me.handle_save_fail(btn, on_error));

    if (can_cancel) {
        d.set_primary_action("Cancel All", () => {
            d.hide();
            frappe.call({
                method: "go1_commerce.accounts.defaults.cancel_all_linked_docs",
                args: {
                    docs: links
                },
                freeze: true,
                async: true,
                callback: (resp) => {
                    if (!resp.exc) {
                        me.reload_doc();
                        me._cancel(btn, callback, on_error, true);
                    }
                }
            });
        });
    }
    d.show();
}