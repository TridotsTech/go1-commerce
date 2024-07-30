//  frappe.treeview_settings['Product Category'] = {
// 	ignore_fields:["parent_product_category"],
// 	root_label: "All Categories",
// 	// get_tree_root: false,
// };

frappe.provide("frappe.treeview_settings")
frappe.treeview_settings['Product Category'] = {
	
	filters: [
		// {
		// 	fieldname: "product_category",
		// 	fieldtype:"Link",
		// 	options: "Product Category",
		// 	label: __("Product Category"),
		// 	default: "All Categories"
		// },
		{
			fieldname: "business",
			fieldtype:"Link",
			options: "Business",
			label: __("Business"),
			default: ""
		}
	],
	get_tree_nodes: "go1_commerce.go1_commerce.doctype.product_category.product_category.get_children",
	add_tree_node: "go1_commerce.go1_commerce.doctype.product_category.product_category.add_node",
	title:"Product Category",
	breadcrumb: "Product Category",
	disable_add_node: false,
	get_tree_root: true,
	root_label: "All Categories",
	show_expand_all: true,
	show_collapse_all: true,
	get_label: function(node) {
		console.log(node)
		if(node.data.label) {
			return node.data.label+ "("+node.data.value+")";
		} else {
			return node.data.value
		}
	},
	ignore_fields:["parent_customer"],
	toolbar: [

		{ toggle_btn: true },
		{
			label:__("Edit"),
			condition: function(node) {
				// return !node.is_root;
				return node
			},
			click: function(node) {
				frappe.set_route("Form", "Product Category", node.data.value);
			}
		},
		{
			label:__("Add"),
			condition: function(node) {
				if(node.data.value=="All Categories"){
					return node.data.value
				}
				else{
					if(node.data.expandable==1){
						return node.data.value
					}
				}
			},
			click: function(node) {
				console.log(node.data)
				this.data = [];
				// console.log(frappe.treeview_settings['Product Category'].treeview)
				// let customer = frappe.treeview_settings['Product Category'].treeview.page.fields_dict.category_name.get_value();
			
				const dialog = new frappe.ui.Dialog({
					title: __("Add Product Category"),
					fields: [
						{
							fieldname: "category_name",
							fieldtype:"Data",
							options: "",
							label: __("Category Name"),
						},
						
						
						{
							fieldname: "col_1",
							fieldtype:"Column Break",
							
						},
					    {
							fieldname: "is_group",
							fieldtype:"Check",
							options: "",
							default:1,
							label: __("Is Group"),
						},
						{
							fieldname: "parent_product_category",
							fieldtype:"Link",
							options: "Product Category",
							label: __("Parent"),
							read_only:1,
							hidden:1
						},
					],
					primary_action: function() {
						dialog.hide();
						console.log(dialog.get_values())
						return frappe.call({
							method: "go1_commerce.go1_commerce.doctype.product_category.product_category.add_customer_withparent",
							args: {
								data: dialog.get_values(),
								parent: node.data.value
							},
							callback: function() { cur_tree.reload_node(cur_tree.root_node); }
						});
						cur_tree.reload_node(cur_tree.root_node);
						
					},
					primary_action_label: __('Create')
				});
				dialog.get_field("parent_product_category").set_value(node.data.value);
				dialog.show();
			}
		},
		{
			label:__("Delete"),
			condition: function(node) { 
				return !node.is_root; 
			},
			click: function(node) {
				frappe.model.delete_doc("Product Category", node.label, function() {
					node.parent.remove();
					cur_tree.reload_node(cur_tree.root_node);
				});
			},
			btnClass: "hidden-xs"
		}
	],
    onload: function(treeview) {

		treeview.page.add_inner_button(__("Collapse All"), function() {
            $('.menu-btn-group').find('ul li a').find('span[data-label="Refresh"]').click();
        });
		treeview.page.add_inner_button(__("List View"), function() {
            frappe.set_route('List', 'Product Category','List');   
        });
		
		frappe.treeview_settings['Product Category'].treeview = {};
		$.extend(frappe.treeview_settings['Product Category'].treeview, treeview);
	}
};