frappe.provide("go1_commerce.setup");

frappe.pages['setup-wizard'].on_page_load = function(wrapper) {
	
};

frappe.setup.on("before_load", function () {
	go1_commerce.setup.slides_settings.map(frappe.setup.add_slide);
});

go1_commerce.setup.slides_settings = [
	{
		
		name: 'domain',
		title: __('Select your Domains'),
		fields: [
			{
				fieldname: 'domains',
				label: __('Domains'),
				fieldtype: 'MultiCheck',
				options: [
					{ "label": __("Restaurant"), "value": "Restaurant" },
					{ "label": __("Single Vendor"), "value": "Single Vendor" },
					{ "label": __("Multi Vendor"), "value": "Multi Vendor" },
					{ "label": __("Purchase"), "value": "Purchase" },
					{ "label": __("Business Deals"), "value": "Business Deals" },
					{ "label": __("SaaS"), "value": "SaaS" },
					{ "label": __("Services"), "value": "Services" }
				], reqd: 1
			},
		],
		
		validate: function () {
			
			frappe.setup.domains = this.values.domains;
			return true;
		},
	},
	{
		name: 'business_setup',
		title: __('Business Setup'),
		fields: [
			{ fieldname: 'business', label: __('Name of your business'), fieldtype: 'Data', reqd: 1 },
			{ fieldname: 'contact_number', fieldtype: 'Data', reqd: 1,  options: 'Phone',  label: __('Contact Number') },
			{ fieldname: 'contact_email', fieldtype: 'Data',  reqd: 1, options: 'Email',  label: __('Contact Email') },
			{ fieldname: 'address', fieldtype: 'Data', reqd: 1, label: __('Address') },
			{ fieldname: 'city', fieldtype: 'Data', reqd: 1, label: __('City') },
			{ fieldname: 'sample_data', fieldtype: 'Check', label: __('Create Sample Records?')}
		]
	}
];
