// Copyright (c) 2019, sivaranjani and contributors
// For license information, please see license.txt

frappe.ui.form.on('Product Review', {
	refresh: function(frm) {
		frm.trigger('multi_upload')
	},
	multi_upload: function(frm) {
		$(frm.fields_dict['img_html'].wrapper).html("");
		if (frm.doc.review_images) {
			var img_html = `<div class="row" id="img-gallery">`;
			$(frm.doc.review_images).each(function(i, v) {
				img_html += `<div id="div${v.idx }" title="${v.name}" class="sortable-div div_${v.name}">
								<div class="col-md-2" id="drag${v.idx}">
									<div style="padding: 15px; class="">
										<img class="img-name" src="${v.image}" title="${v.image_name}"
																id="${v.name1}" style="height:100px;">
										<a class="img-close" id="${v.name}" style="display:none;
											cursor: pointer;font-size: 21px;float: right;font-weight: bold;
											line-height: 1;color: #000;text-shadow: 0 1px 0 #fff;opacity:.2;">
											×
										</a>
										<a data-id="${v.name}" class="edit" style="display:none;font-size:15px;
																					padding:5px;color:#a2a0a0;">
											<i class="fa fa-pencil-square-o" aria-hidden="true"></i>
										</a>
										<label style="display:none !important;font-size: 10px;font-weight: 200;">
											Is Cover Image
											<input type="checkbox" data-fieldname="is_cover_image" style="float:left;
															margin-right: 6px;margin-top: 0px;display:none !important">
										</label>
										<input type="text" data-fieldtype="Data" data-fieldname="image_title" 
											value="${v.name1}" style="margin-top: 5px;width: 112px;display:none !important" 
																										placeholder="Name">
										<a class="save" data-id="${v.name}" style="font-size:15px;padding:5px;
																					color:#a2a0a0;display:none">
											<i class="fa fa-save" aria-hidden="true"></i>
										</a>
									</div>
								</div>
							</div> `;
			})
			img_html += '</div>';
			$(frm.fields_dict['img_html'].wrapper).html(img_html);
		}
	}
})
