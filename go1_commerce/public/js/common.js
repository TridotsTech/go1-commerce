


$('.album-u-cancel').on("click", function(e){
  $('#mains').css("width", '100%');
	$('.album-Dashboard-FileCard').hide();
	 $("#mySidebars").css("width" , "0");
  	$("#mains").css("marginLeft","0");
})

function openImageModel(e){
   $('#mains').css("width", '68%');
	cur_frm.set_df_property("album_html","hidden", 1);
	$('.album-Dashboard-FileCard').show();
	$("#mySidebars").css("width","400px");
  	$("#mains").css("marginLeft","400px");
  	var img_id = $(e).attr("data-imgid");
	console.log("-----open image-------")
	console.log(img_id)
	console.log(cur_frm.docname)
  	frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.get_gallery_list',
            args: {
                "parent":cur_frm.docname,
                "name":img_id
            },
            async: false,
            callback: function(r) {
		console.log(r)
            	if(r){
            		var data = r.message;
            		if(data.length > 0){
            			$('.album-DashboardContent-titleFile').text(data[0].image);
					  	$("#mySidebars").find('.album-Dashboard-FileCard-actionsBtn').attr("data-name",data[0].name);
					  	$('#album-Dashboard-FileCard-input-name').val(data[0].name1);
					  	$('#album-Dashboard-FileCard-input-caption').val(data[0].caption);
					  	$('.album-DashboardItem-previewImg').attr("src",data[0].file_url);
					  	$('.album-DashboardItem-previewImg').attr("alt",data[0].file_url);
            		}
            		
            	}
            }
        })
  	
}


function removeImageModel(e){
  var dataname = $(e).attr("data-name");
  if(dataname){
     frappe.model.delete_doc("Product Image", dataname, function(r) {
       $('#mains').css("width", '100%');
        cur_frm.reload_doc();
    });
  }
}
function saveImageModel(e){
	$('#mains').css("width", '100%');
	var dataname = $(e).attr("data-name");
	var img_name = $('#album-Dashboard-FileCard-input-name').val();
  	var img_caption = $('#album-Dashboard-FileCard-input-caption').val();
	if(dataname){
		 frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.save_gallery_changes',
            args: {
                "data": {
                    doc_type:"Product Image",
                    doc_name:dataname,
                    img_name: img_name,
                    img_caption: img_caption
                }
            },
            async: false,
            callback: function(r) {
            	if(r){
            		cur_frm.reload_doc();
	            	
            	}
            }
        })
	}
}
$('.album-DashboardContent-back').on("click", function(){
	$('.album-Dashboard-FileCard').show();
	 $("#mySidebars").css("width","400px");
  		$("#mains").css("marginLeft","50px");
})
function closeNav(){
  $('#mains').css("width", '100%');
	$('.album-Dashboard-FileCard').show();
	$("#mySidebars").css("width","200px");
  	$("#mains").css("marginLeft","50px");
}

$(document).ready(function () {
console.log("--card------------")
setTimeout(function(){ 
	$('.album-Dashboard-FileCard').hide();
 }, 3000);
	

})
