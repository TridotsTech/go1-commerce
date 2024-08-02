var UppyUploadComponent = Class.extend({
    init: function(opts) {
        this.frm = opts.frm;
        this.htmlfield = opts.htmlfield;
        this.parentfield = opts.parentfield;
        this.childdoctype = opts.childdoctype;
        this.childdocname = opts.childdocname;
        this.make();
    },
    make: function() {
        this.image_dialog();
    },
    image_dialog: function() {
        let me = this;
        frappe.run_serially([
            () => { 
                me.get_image_album(me.childdoctype, me.childdocname);
            },
            () => { me.show_img_dialog(); }
        ])
    },
    show_img_dialog: function() {
        let me = this;
        this.imagedialog = new frappe.ui.Dialog({
            title: __("Pick Image"),
            fields: [
                { "fieldname": "tab_html", "fieldtype": "HTML" },
                { "fieldname": "sec_1", "fieldtype": "Section Break" },
                { "fieldname": "upload_img", "fieldtype": "HTML" },
                { "fieldname": "sec_2", "fieldtype": "Section Break" },
                { "fieldname": "image_gallery", "fieldtype": "HTML" }
            ]
        });
        this.imagedialog.set_primary_action(__('Save'), function() {
            let active_tab = me.imagedialog.fields_dict.tab_html.$wrapper.find('li.active').attr('data-id');
            let image = "";
            if (active_tab == '2') {
                image = me.picked_image;
            } else if (active_tab == '1') {
                image = me.uploaded_image;
            }
            $(me.list_section_data).each(function(k, v) {
                if (v.idx == rec.idx) {
                    v.image = image;
                }
            });
            me.imagedialog.hide();
        });
        this.imagedialog.show();
        this.gallery_tab_html();
        this.uploader_component();
        this.gallery_html();
        this.imagedialog.$wrapper.find('.modal-dialog').css("width", "800px");
        this.imagedialog.$wrapper.find('.form-section').css("border-bottom", "0");
    },
    get_image_album: function(dt, dn) {
        let me = this;
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.get_doc_images',
            args: {
                dt: dt,
                dn: dn
            },
            async: false,
            callback: function(r) {
                if (r.message) {
                    me.doc_files = r.message;
                } else {
                    me.doc_files = [];
                }
            }
        })
        frappe.call({
            method: 'frappe.core.doctype.file.file.get_files_in_folder',
            args: {
               folder:"Home"
            },
            async: false,
            callback: function(r) {
                if (r.message) {
                    me.gallery_data = r.message;
                } else {
                    me.gallery_data = [];
                }
            }
        })
        
    },
    gallery_tab_html: function() {
        let me = this;
        let tab_html = this.imagedialog.fields_dict.tab_html.$wrapper.empty();
        $(`<div class="gal-tabs">
            <ul>
                <li class="active" data-id="1">${__("Upload Image")}</li>
                <li data-id="2">${__("Pick Image")}</li>
            </ul>
        </div>
        <style>
            div[data-fieldname="tab_html"]{ margin-bottom: 0; }
            div[data-fieldname="tab_html"] .gal-tabs{ text-align: center; }
            div[data-fieldname="tab_html"] .gal-tabs ul{display: inline-flex;list-style:none;}
            div[data-fieldname="tab_html"] .gal-tabs ul li{padding: 5px 25px;cursor: pointer;font-size: 15px;font-weight: 500;}
            div[data-fieldname="tab_html"] .gal-tabs ul li.active{border-bottom: 2px solid #1b8fdb}
           
        </style>`).appendTo(tab_html);
        this.imagedialog.fields_dict.sec_2.wrapper.hide();
        tab_html.find('li').click(function() {
            tab_html.find('li').removeClass('active');
            if ($(this).attr('data-id') == '1') {
                me.imagedialog.fields_dict.sec_2.wrapper.hide();
                me.imagedialog.fields_dict.sec_1.wrapper.show();
                tab_html.find('li[data-id="1"]').addClass('active');
            } else {
                me.imagedialog.fields_dict.sec_1.wrapper.hide();
                me.imagedialog.fields_dict.sec_2.wrapper.show();
                tab_html.find('li[data-id="2"]').addClass('active');
            }
        });
    },
    gallery_html: function() {
        let me = this;
        let gallery_html = this.imagedialog.fields_dict.image_gallery.$wrapper.empty();
        if (this.doc_files && this.doc_files.length > 0) {
            $(`<div class="gallery row"></div>
                <style>
                div[data-fieldname="image_gallery"] .gallery .gal-items{position: relative;}
                div[data-fieldname="image_gallery"] .gallery .gal-items img{
                    position: absolute; top: 50%; left: 50%; vertical-align: middle;
                    transform: translate(-50%, -50%); width: auto; height: 90%;
                }
                div[data-fieldname="image_gallery"] .gallery .gal-items.active{border: 2px solid #0bc50b;}
                </style>`).appendTo(gallery_html);
            this.doc_files.map(f => {
                console.log(f)
                let row = $(`<div class="col-md-3 gal-items" style="margin-bottom: 10px; height: 100px;"><img src="${f.product_image}" /></div>`);
                gallery_html.find('.gallery').append(row);
                row.click(function() {
                    gallery_html.find('.gal-items').removeClass('active');
                    row.addClass('active');
                    me.picked_image = f.list_image;
                });
            });
            gallery_html.find('.gallery').slimScroll({
                height: 300
            })
        } else {
            gallery_html.append(`<div style="text-align: center;background: #ddd;padding: 10%;font-size: 20px;border: 1px solid #ccc;border-radius: 4px;">No images found!</div>`)
        }
    },
    uploader_component: function() {
        let me = this;
        let uploader = this.imagedialog.fields_dict.upload_img.$wrapper.empty();
        let random = parseInt(Math.random() * 10000);
        uploader.append(`<div id="uploader${random}"></div><div id="progress${random}"></div><style> .uppy-DragDrop-inner {padding: 0px;}
        .uppy-DragDrop-inner svg{display:none;}</style>`);
        setTimeout(function() {
            me.upload_component(`#uploader${random}`, `#progress${random}`);
        }, 500);

    },
    upload_component: function(target, progress) {
        let me = this;
        var uppy = Uppy.Core({
                restrictions: {
                    maxFileSize: 250000,
                    maxNumberOfFiles: 1,
                    allowedFileTypes: ['image/*', '.jpg', '.png', '.jpeg', '.gif']
                },
                meta: {
                    doctype: 'Page Section',
                    docname: me.section
                }
            })
            .use(Uppy.DragDrop, {
                target: target,
                inline: true,
                note: 'Image only up to 250 KB'
            })
            .use(Uppy.XHRUpload, {
                endpoint: window.location.origin + '/api/method/go1_commerce.cms.doctype.web_page_builder.web_page_builder.upload_img',
                method: 'post',
                formData: true,
                fieldname: 'file',
                headers: {
                    'X-Frappe-CSRF-Token': frappe.csrf_token
                }
            })
            .use(Uppy.StatusBar, {
                target: progress,
                hideUploadButton: false,
                hideAfterFinish: false
            })
            .on('upload-success', function(file, response) {
                if (response.status == 200) {
                    me.uploaded_image = response.body.message.file_url;
                    me.imagedialog.$wrapper.find('.modal-header .btn-primary').trigger('click');
                }
            });
    }
})
