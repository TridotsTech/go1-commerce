$(function() {
	pageview_fn();
   
});

frappe.provide('core.update_default')

core.update_default = function(parent, value, key='business_setup') {
	frappe.call({
		method: 'go1_commerce.utils.setup.update_business_default',
		args: {
			parent: parent,
			value: value,
			key: key
		},
		callback: function(r) {

		}
	})
}

var pageview_fn = function() {
    let pageview = frappe.views.pageview;
    pageview.show = function(name) {

        if(!name)
        	name = 'dashboard';
        frappe.model.with_doctype("Page", function() {
            frappe.views.pageview.with_page(name, function(r) {
                if(r && r.exc) {
                    if(!r['403'])
                        frappe.show_not_found(name);
                } else if(!frappe.pages[name]) {
                    new frappe.views.Page(name);
                }
                frappe.container.change_to(name);
            });
        });
    }
    frappe.views.pageview = pageview;
}

frappe.provide('core.gettingStarted');
core.gettingStarted = class gettingStarted {
    constructor(opts) {
        $.extend(this, opts);
        this.wrapper.empty();
        this.progress = 0;
        this.business = frappe.boot.user.defaults.business;
        this.show();
    }

    show() {
        this.menu_items = this.get_menu_list();
        if(this.menu_items.length == 0)
        	return;
        $(`<div>
                <div class="container-fluid">
                    <div class="row">
                        <div class="col-md-12 pad-0">
                            <div class="head-title">${__('Getting Started')}</div>
                        </div>
                    </div>
                </div>
                <div class="container-fluid white-bg">
                    <div class="row">
                        <div class="col-md-4 pad-0" style="border-right: 1px solid #ddd;">
                            <ul class="menu-items"></ul>
                            <div class="skip"><a>${__("Skip getting started")}</a></div>
                        </div>
                        <div class="col-md-8 pad-0">
                            <div class="item-desc"></div>
                        </div>
                    </div>
                </div>
            </div>
            <style>
                #page-dashboard .getting-started {
                    margin-bottom: 15px;
                }
                #page-dashboard .getting-started .container-fluid {
                    max-width: 1000px;
                }
                #page-dashboard .getting-started .pad-0 {
                    padding: 0;
                }
                #page-dashboard .getting-started .head-title {
                    font-weight: 600;
                    font-size: 15px;
                    margin-bottom: 10px;
                }
                #page-dashboard .getting-started .white-bg {
                    background: #fff;
                }
                #page-dashboard .getting-started .menu-items {
                    list-style: none;
                    padding: 10px 15px;
                    margin: 0;
                }
                #page-dashboard .getting-started .desc-list {
                    display: none;
                    padding: 15px;
                    min-height: 300px;
                    background-size: 50%;
                    background-position: bottom right;
                    background-repeat: no-repeat;
                }
                #page-dashboard .getting-started .desc-list .txt-type1 {
                    font-weight: 600;
                    font-size: 15px;
                }
                #page-dashboard .getting-started .desc-list .txt-type2 {
                    margin: 15px 0;
                    font-size: 14px;
                    min-height: 60px;
                    max-width: 400px;
                }
                #page-dashboard .getting-started .desc-list.active {
                    display: block;
                }
                #page-dashboard .getting-started .menu-items .active-div {
                    display: none;
                }
                #page-dashboard .getting-started .menu-items li.verified .count-div {
                    display: none;
                }
                #page-dashboard .getting-started .menu-items li.verified .active-div {
                    display: inherit;
                }
                #page-dashboard .getting-started .menu-items li a {
                    text-decoration: none;
                    font-size: 14px;
                }
                #page-dashboard .getting-started .menu-items li.active a {
                    font-weight: 600;
                }
                #page-dashboard .getting-started .menu-items .cg {
                    background: #eee;
                    border-radius: 50%;
                    border: 1px solid #ddd;
                    margin-right: 5px;
                    padding: 6px 11px;
                    font-size: 12px;
                }
                #page-dashboard .getting-started .menu-items .active-div {
                    padding: 8px;
                    color: #16b116;
                    border-color: #16b116;
                    background: #fff;
                }
                #page-dashboard .getting-started .skip {
                    padding: 15px;
                    margin-top: 10px;
                }
                #page-dashboard .getting-started .skip a {
                    text-decoration: none;
                    color: #1b8fdb;
                    font-size: 12px;
                }
            </style>`).appendTo(this.wrapper);
        let me = this;
        this.wrapper.find('.close-div, .skip a').on('click', function () {
            me.wrapper.empty();
        });
        this.$menuDiv = this.wrapper.find('.menu-items');
        this.$contentDiv = this.wrapper.find('.item-desc');
        this.$progressDiv = this.wrapper.find('.progress');
        
        this.menu_items.map(f => {
            let row = $(`<li data-key="${f.key}" class="${(f.idx == 1) ? 'active' : ''}" style="padding: 10px 0;">
                <a><span class="count-div cg">${f.idx}</span><span class="active-div cg fa fa-check"></span> ${__(f.label)}</a>
            </li>`);
            row.click(function() {
                me.$contentDiv.find('.desc-list').each(function() {
                    $(this).removeClass('active');
                });
                me.$menuDiv.find('li').each(function() {
                    $(this).removeClass('active');
                });
                row.addClass('active');
                me.$contentDiv.find('.desc-list[data-key="' + f.key + '"]').addClass('active');
            })
            row.appendTo(this.$menuDiv);
            $(`<div class="desc-list ${(f.idx == 1) ? 'active' : ''}" data-key="${f.key}">
                <div class="txt-type1">${__(f.section_title)}</div>    
                <div class="txt-type2">${__(f.section_desc)}</div>
                <div>
                    <button onclick="${f.click}" class="btn btn-primary">${__(f.button_text)}</button>
                </div>   
            </div>`).appendTo(this.$contentDiv);
            if(f.bg_image) {
                this.$contentDiv.find('div[data-key="' + f.key + '"]').css('background-image', 'url("' + f.bg_image + '")');
            }
        });
        if(frappe.boot.sysdefaults.business_defaults && frappe.boot.sysdefaults.business_defaults[this.business]) {
            let progress = frappe.boot.sysdefaults.business_defaults[this.business];
            progress = JSON.parse(progress);
            let current_progress = progress.length * 100 / this.menu_items.length;
            this.progress = parseInt(current_progress);
            if(this.$progressDiv)
                this.set_progress();
            $(progress).each((k, v) => {
                this.$menuDiv.find('li[data-key="' + v + '"]').addClass('verified');
            })
        }
    }

    get_menu_list() {
    	
    		return []
    }

    set_progress() {
        this.$progressDiv.html(`<div class="progress-bar" role="progressbar" style="width: ${this.progress}%;" aria-valuenow="${this.progress}" aria-valuemin="0" aria-valuemax="100"></div>`)
    }
}
