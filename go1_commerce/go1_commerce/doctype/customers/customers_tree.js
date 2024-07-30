frappe.provide("frappe.treeview_settings")

frappe.treeview_settings['Customers'] = {
	filters: [
		{
			fieldname: "business",
			fieldtype:"Link",
			options: "Business",
			label: __("Business"),
			default: ""
		}
	],
	get_tree_nodes: "go1_commerce.go1_commerce.doctype.customers.customers.get_children",
	add_tree_node: "go1_commerce.go1_commerce.doctype.customers.customers.add_node",
	title:"Customers",
	breadcrumb: "Customers",
	disable_add_node: false,
	get_tree_root: true,
	root_label: "All Customers",
	show_expand_all: true,
	get_label: function(node) {
		if(node.data.title) {
			return node.data.title+ "("+node.data.value+")";
		} else {
			return node.data.value
		}
	},
	toolbar: [
		{ toggle_btn: true },
		{
			label:__("Edit"),
			condition: function(node) {
				return !node.is_root;
			},
			click: function(node) {
				frappe.set_route("Form", "Customers", node.data.value);
			}
		},
		{
			label:__("Add"),
			condition: function(node) {
				return node.expandable;
			},
			click: function(node) {
				this.data = [];
				let business = frappe.treeview_settings['Customers'].treeview.page.fields_dict.business.get_value();
				const dialog = new frappe.ui.Dialog({
					title: __("Add Customers"),
					fields: [
						{
							fieldname: "first_name",
							fieldtype:"Data",
							options: "",
							label: __("First Name"),
						},
						{
							fieldname: "phone",
							fieldtype:"Data",
							options: "",
							label: __("Phone"),
						},
						{
							fieldname: "is_group",
							fieldtype:"Check",
							options: "",
							label: __("Is Group"),
						},
						{
							fieldname: "col_1",
							fieldtype:"Column Break",
							
						},
						{
							fieldname: "last_name",
							fieldtype:"Data",
							options: "",
							label: __("Last Name"),
						},
						{
							fieldname: "email",
							fieldtype:"Data",
							options: "Email",
							label: __("Email ID"),
						},
						{
							fieldname: "business",
							fieldtype:"Link",
							options: "Business",
							label: __("Business"),
							read_only:1,
							hidden:1
						},
					],
					primary_action: function() {
						dialog.hide();
						return frappe.call({
							method: "go1_commerce.go1_commerce.doctype.customers.customers.add_customer_withparent",
							args: {
								data: dialog.get_values(),
								parent: node.data.value
							},
							callback: function() { }
						});
						cur_tree.reload_node(cur_tree.root_node);
						
					},
					primary_action_label: __('Create')
				});
				dialog.get_field("business").set_value(business);
				dialog.show();
			}
		},
		{
			label:__("Delete"),
			condition: function(node) { 
				return !node.is_root; 
			},
			click: function(node) {
				frappe.model.delete_doc("Customers", node.label, function() {
					node.parent.remove();
					cur_tree.reload_node(cur_tree.root_node);
				});
			},
			btnClass: "hidden-xs"
		}
	],
	menu_items: [
		{
			label: __("New Customer"),
			action: function() {
				frappe.new_doc("Customers", true);
			},
			condition: 'frappe.boot.user.can_create.indexOf("Customers") !== -1'
		},
		{
				label: __('View List'),
				action: function() {
					frappe.set_route('List', "Customers");
				}
		}
	],
	onload: function(treeview) {
		treeview.page.add_inner_button(__("List View"), function() {
	            frappe.set_route('List', 'Customers','List');
	        });

		frappe.treeview_settings['Customers'].treeview = {};
		$.extend(frappe.treeview_settings['Customers'].treeview, treeview);
		function get_company() {
			return treeview.page.fields_dict.business.get_value();
		}
	},
	post_render: function() {
	},
	onrender: function(node) {
		let me = this;
		if(node.is_root && node.data.value!="") {
			frappe.model.with_doc("Customers", node.data.value, function() {
				var cust = frappe.model.get_doc("Customers", node.data.value);
				node.data.first_name = cust.first_name || "";
				node.data.last_name = cust.last_name || "";
				node.data.email = cust.email || "";
				node.data.phone = cust.phone || "";
			});
		}
	},
	refresh: function(node) {
		let me = this;
		if(node.is_root && node.data.value!="") {
			frappe.model.with_doc("Customers", node.data.value, function() {
				var cust = frappe.model.get_doc("Customers", node.data.value);
				node.data.first_name = cust.first_name || "";
				node.data.last_name = cust.last_name || "";
				node.data.email = cust.email || "";
				node.data.phone = cust.phone || "";
			});
		}

	},
	view_template: 'customer_preview',
};