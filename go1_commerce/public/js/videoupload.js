function video_files(random, link_doctype, link_name, parentfield, video_doctype, child_docname) {
	$.getScript('https://transloadit.edgly.net/releases/uppy/v0.30.4/uppy.min.js', function () {
		var uppy = Uppy.Core({
				restrictions:{
					maxFileSize: 20000000,
					allowedFileTypes:['video/*','.mp4','.webm']
				}
			})
			.use(Uppy.Dashboard, {
				inline: true,
				target: '#drag-drop-area' + random,
				disablePageScrollWhenModalOpen: true,
				disableInformer: false,
				height: 450,
				hideRetryButton: false,
				animateOpenClose: true,
				closeModalOnClickOutside: false,
				replaceTargetContent:false,
				showProgressDetails:true,
				hideProgressAfterFinish:true,
				disableStatusBar:false,
				note: 'Videos only, up to 20 MB',
				locale:{
					strings:{
						dropPaste: 'Drop files here or %{browse}',
					}					
				}				
			})
		var filelists = [];
		uppy.on('upload', (data, file) => {
			$("<h4 class='msg'>Uploading. Please wait.......</h4>").appendTo(".uppy-Informer");
			$('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
			let files_count=uppy.getFiles().length;
			let count=0;
			let all_files=uppy.getFiles();
			$.each(filelists[0][0].files, function (i, s) {
				let check_deleted = all_files.find(obj=>obj.name==s.name);
				if(check_deleted){
					$('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
					var reader = new FileReader();
					let date = new Date();
					let datetime = date.toLocaleString().replace(/ /g, '');
					let cur_time = datetime.replace(/\//g, '-');
					let filename = check_deleted.name.split('.' + check_deleted.extension)[0] + '-' + cur_time + '.' + check_deleted.extension;
					reader.onload = function (e) {
						$('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
						var upload_doc = localStorage.getItem("upload_tab");
						var upload_name = localStorage.getItem("upload_doc");
						frappe.call({
							method: 'uploadfile',
							args: {
								from_form: 1,
								doctype: link_doctype,
								docname: link_name,
								is_private: 0,
								filename: filename,
								file_url: '',
								file_size: s.size,
								filedata: e.target.result,
								upload_doc: upload_doc
							},
							async: false,
							callback: function (r) {
								count = count + 1;
								$('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
								if(child_docname)
									update_attribute_video(r.message.file_url, child_docname, count, files_count, link_doctype)
								else
									update_video(r, s, upload_doc, files_count, count, parentfield, video_doctype)
							}
						})
					};
					reader.readAsDataURL(s);
					uppy.reset();
				}
			});
		})
		uppy.on('file-added', (file) => {			
			$('.uppy-DashboardContent-addMore').css('display','none');
		})
		$(document).ready(function () {
			$('.uppy-DashboardAddFiles-info').find('.uppy-Dashboard-poweredBy').css("display", "none");
			$('.uppy-Dashboard-progressindicators').find('.uppy-StatusBar-actions button').attr("id", "uploadbtn");
			$('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
			$('.uppy-DashboardAddFiles').on('drop',function(e){
				$("input[type=file]").prop("files", e.originalEvent.dataTransfer.files);
				$("input[type=file]").trigger('change')
				$('.uppy-DashboardContent-addMore').css('display','none');
			})
			$('.uppy-DashboardContent-addMore').css('display','none');
		});
		$('input[type=file]').change(function () {
			filelists.push($(this))
			var input = $(this);
		});
	})
}

function update_video(r, s, upload_doc, files_count, count, parentfield, video_doctype){
	frappe.call({
		method: 'go1_commerce.go1_commerce.api.update_videoto_file',
		args: {
			file_name: r.message.file_name,
			upload_doc: upload_doc,
			docname: cur_frm.docname,
			file_type: s.type,
			file_path: r.message.file_url,
			name: r.message.name,
			total_files: files_count,
			current_file: count,
			doctype: cur_frm.doctype,
			parentfield: parentfield,
			video_doctype: video_doctype
		},
		async: false,
		callback: function (f) {
			cur_frm.isloaded = 1;
			$(".menu-btn-group .dropdown-menu li a").each(function () {
				if ($(this).text() == "Reload") {
					$(this).click();
				}
			});										
			frappe.show_alert(__("Video Added!"));
			if(count == files_count){
				cur_dialog.hide();
				cur_frm.reload_doc();
			}
		}
	});
}

function update_attribute_video(filename, docname, count, files_count, link_doctype){

	frappe.call({
                method: "go1_commerce.go1_commerce.doctype.product.product.insert_attribute_option_video",
                args: {
                    "option_id": docname,
                    "video_id": filename,
                    "video_type":'Other'
                },

                callback: function(r) {
                    frappe.show_alert(__("Video Added!"));
					if(count == files_count){
						cur_dialog.hide();
						setTimeout(function() {
							var doctype = null;
							if(link_doctype=="Product Variant Combination"){
								doctype = "Product Variant Combination"
							}
							EditAttributeOption(docname, doctype);
			            }, 100);
					}
                }

            })
}