function upload_files(random, link_doctype, link_name, parentfield, image_doctype, child_docname) {
	//getScripts(['https://releases.transloadit.com/uppy/v1.22.0/uppy.min.js'], function () {
	$.getScript('https://releases.transloadit.com/uppy/v1.22.0/uppy.min.js', function () {
	 loadCss("https://releases.transloadit.com/uppy/v1.22.0/uppy.min.css")
		console.log( $('#imgtab'))
		console.log($('#imgtab').find('#London'))
		console.log( $('#imgtab').find('#London').find('#drag-drop-area' + random))

		const Dashboard = Uppy.Dashboard
		const GoogleDrive = Uppy.GoogleDrive
		const Dropbox = Uppy.Dropbox
		const Instagram = Uppy.Instagram
		const Facebook = Uppy.Facebook
		const OneDrive = Uppy.OneDrive
		const Url = Uppy.Url
		const Webcam = Uppy.Webcam
		const ScreenCapture = Uppy.ScreenCapture
		const ImageEditor = Uppy.ImageEditor
		const Tus = Uppy.Tus
		const XHRUpload = Uppy.XHRUpload
		const ThumbnailGenerator = Uppy.ThumbnailGenerator
		
		var uppy = Uppy.Core({
				restrictions:{
					maxFileSize: 1000000,
					allowedFileTypes:['image/*','.jpg','.png','.jpeg','.gif','.webp','.svg']
				}
			})
			.use(Dashboard, {
				
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
				note: 'Images only, up to 1 MB',
				locale:{
					strings:{
						dropPaste: 'Drop files here or %{browse}',
					}					
				}				
			})
			.use(XHRUpload, {
				endpoint: window.location.origin + '/api/method/go1_commerce.go1_commerce.doctype.product.product.upload_img',
				method: 'post',
				formData: true,
				fieldname: 'files[]',
				headers: {
				    'X-Frappe-CSRF-Token': frappe.csrf_token
				}
			    })
			uppy.use(ThumbnailGenerator, {
				  id: 'ThumbnailGenerator',
				  thumbnailWidth: 200,
				  thumbnailHeight: 200,
				  thumbnailType: 'image/jpeg',
				  waitForThumbnailsBeforeUpload: false
				})
		
		
		uppy.use(Url, { target: Dashboard, companionUrl: "https://node.gofisto.com", host: window.location.origin  })
	   	uppy.use(GoogleDrive, { target: Dashboard, companionUrl: "https://node.gofisto.com" })
	        uppy.use(Dropbox, { target: Dashboard, companionUrl: "https://node.gofisto.com" })
		uppy.use(Instagram, { target: Dashboard, companionUrl: "https://node.gofisto.com" })
		uppy.use(Facebook, { target: Dashboard, companionUrl: "https://node.gofisto.com" })
		uppy.use(OneDrive, { target: Dashboard, companionUrl: "https://node.gofisto.com" })
		uppy.use(Webcam, {countdown: false,mirror: true,facingMode: 'user',target: Dashboard})
		
		
		uppy.use(Tus, { endpoint: "https://node.gofisto.com" })
		var filelists = [];
		uppy.on('upload-success', (file, response) => {
	          console.log("----------upload-success--------------")
		  console.log(file.name, response.uploadURL)
		  var img = new Image()
		  img.width = 300
		  img.alt = file.id
		  img.src = response.uploadURL
		  document.body.appendChild(img)
		})
		uppy.on('complete', (result) => {
		  console.log('successful files:', result.successful)
		  console.log('failed files:', result.failed)
		})
		uppy.on('error', (error) => {
			$('.uppy-u-reset.uppy-StatusBar-actionCircleBtn').click();
		   console.log("----------error--------------")
		 
		})
		uppy.on('reset-progress', () => {
			console.log("----------reset-progress--------------")
		  
		})
		uppy.on('restriction-failed', (file, error) => {
			console.log("----------restriction-failed--------------")
		  
		})
		uppy.on('upload-retry', (fileID) => {
		  console.log('upload retried:', fileID)
		})
		uppy.on('upload', (data, file) => {
			console.log("----------upload--------------")
			console.log(data)
			console.log(file)
			$("<h4 class='msg'>Uploading. Please wait.......</h4>").appendTo(".uppy-Informer");
			$('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
			let files_count=uppy.getFiles().length;
			console.log(files_count)
			let count=0;
			let all_files=uppy.getFiles();
			console.log(all_files)
			console.log(filelists)
			$.each(all_files, function (i, s) {
				let check_deleted = all_files.find(obj=>obj.name);
				console.log("-check-----")
				console.log(check_deleted)
				console.log(check_deleted.preview)
				if(check_deleted){
					$('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
					console.log(check_deleted)
					var url = s.preview
					var imgname = s.name
					var imgtype = s.type
					console.log(url)
					
					console.log("------blob------------")
					let date = new Date();
					let datetime = date.toLocaleString().replace(/ /g, '');
					let cur_time = datetime.replace(/\//g, '-');
					console.log(check_deleted.name.split('.' + check_deleted.extension))
					let filename = check_deleted.name.split('.' + check_deleted.extension)[0] + '-' + cur_time + '.' + check_deleted.extension;
					console.log("------blob----1--------")
					imageToBase64 = (URL) => {
						console.log("------blob-----2-------")
					    let image;
					    image = new Image();
					    image.crossOrigin = 'Anonymous';
					    image.addEventListener('load', function() {
						let canvas = document.createElement('canvas');
						let context = canvas.getContext('2d');
						context.drawImage(image, 0, 0);
						console.log("------0------")
						try {
						    console.log(canvas.toDataURL(imgtype))
						    $('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
							var upload_doc = localStorage.getItem("upload_tab");
							var upload_name = localStorage.getItem("upload_doc");
							console.log("------1------")
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
									filedata: canvas.toDataURL(imgtype),
									upload_doc: upload_doc
								},
								async: false,
								callback: function (r) {
									console.log(r)
									count = count + 1;
									$('.uppy-Dashboard-progressindicators').find('.uppy-Informer p').css("display", "none");
									if(child_docname)
										update_attribute_image(r.message.name, image_doctype, child_docname, count, files_count)
									else
										update_image(r, s, upload_doc, files_count, count, parentfield, image_doctype)
								}
							})
							console.log("------2------")
						    localStorage.setItem('saved-image-example', canvas.toDataURL(imgtype));
						} catch (err) {
						    console.error(err)
						}
					    });
					    image.src = URL;
					};
					
					uppy.reset();
				}
				console.log("------blob----00--------")
				imageToBase64(url)
			})
			
		})
		uppy.on('file-added', (file) => {
			console.log("----------file-added--------------")			
			$('.uppy-DashboardContent-addMore').css('display','none');
		})
		uppy.on('thumbnail:generated', (file, preview) => {
			console.log("-----------thumbnail------------");
			  const img = document.createElement('img')
			  img.src = preview
			  img.width = 100
			  document.body.appendChild(img)
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
			console.log($(this))
			filelists.push($(this))
			var input = $(this);
		});
	})
}

async function getFileFromUrl(url, name, type = 'image/jpeg'){
  const response = await fetch(url);
  const data = await response.blob();
  return new File([data], name, {
    type: response.headers.get('content-type') || defaultType,
  });
}

function update_image(r, s, upload_doc, files_count, count, parentfield, image_doctype){
	
	frappe.call({
		method: 'go1_commerce.go1_commerce.v2.product.update_to_file',
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
			image_doctype: image_doctype
		},
		async: false,
		callback: function (f) {
			cur_frm.isloaded = 1;
			$(".menu-btn-group .dropdown-menu li a").each(function () {
				if ($(this).text() == "Reload") {
					$(this).click();
				}
			});										
			frappe.show_alert(__("Image Added!"));
			if(count == files_count){
				cur_dialog.hide();
				cur_frm.reload_doc();
			}
		}
	});
}

function update_attribute_image(filename, doctype, docname, count, files_count){
	frappe.call({
		method: 'go1_commerce.go1_commerce.api.update_attribute_images',
		args:{
			name: filename,
			dt: doctype,
			dn: docname
		},
		async: false,
		callback: function(r){
			frappe.show_alert(__("Image Added!"));
			if(count == files_count){
				cur_dialog.hide();
				EditAttributeOption(docname);
			}			
		}
	})
}
function loadCss(filename) {
    var cssNode = document.createElement("link");
    cssNode.setAttribute("rel", "stylesheet");
    cssNode.setAttribute("type", "text/css");
    cssNode.setAttribute("href", filename);
    document.getElementsByTagName("head")[0].appendChild(cssNode);
}
document.getElementById("defaultOpen").click();
function openCity(evt, cityName) {
  var i, tabcontent, tablinks;
  tabcontent = document.getElementsByClassName("tabcontent");
  for (i = 0; i < tabcontent.length; i++) {
    tabcontent[i].style.display = "none";
  }
  tablinks = document.getElementsByClassName("tablinks");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].className.replace(" active", "");
  }
  document.getElementById(cityName).style.display = "block";
  evt.currentTarget.className += " active";
}
function getScripts(scripts, callback) {
    var progress = 0;
    scripts.forEach(function(script) { 
        $.getScript(script, function () {
            if (++progress == scripts.length) callback();
        }); 
    });
}



