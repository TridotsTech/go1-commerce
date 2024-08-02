function validateAttributeOptionForm() {
    if ($("input[data-fieldname='option_value']").val() == "") {
        frappe.msgprint("Option Value is required");
        return false;
    }
    if ($("input[data-fieldname='display_order_no']").val() == "") {
        frappe.msgprint("Display Order is required");
        return false;
    }
    if ($("input[data-fieldname='price_adjustment']").val() == "") {
        frappe.msgprint("Price Adjustment is required");
        return false;
    }
    return true;
}
function EditAttributeOption(optionId, doctype) {
    var field1 = cur_dialog.get_field("sec1")
    if(field1){
      field1.df.hidden = 0;
      field1.refresh();
    }
   

    if(!doctype){
        doctype = "Product Attribute Option"
    }
    $("#hdnSelectedDoc").val();
    let image = $("#tr-" + optionId).attr('data-image');
     $("#hdnAttributeOptionid").val(optionId);
     if (image != undefined && image != null && image != 'null' && image != 0 && image != "") {
         let html = '<img class="img-responsive attach-image-display" src="' + image + '" /><div class="img-overlay">\
         <span class="overlay-text">Change</span></div>';
         $("div[data-fieldname='image']").find('.missing-image').hide();
         $("div[data-fieldname='image']").find('.img-container').show();
         $("div[data-fieldname='image']").find('.img-container').next().show();
         $("div[data-fieldname='image']").find('.img-container').html(html)
         $("div[data-fieldname='image']").find('.attached-file').show();
         $('div[data-fieldname="image"]').find('.attached-file-link').text('');
         $("div[data-fieldname='image']").find('.attached-file-link').text(image)
     }
     else{
         $('div[data-fieldname="image"]').find('.attached-file-link').text('')
         $('div[data-fieldname="image"]').find('.img-container').find('img').attr('src','');
         $("div[data-fieldname='image']").find('.missing-image').show();
         $("div[data-fieldname='image']").find('.img-container').hide();
         $("div[data-fieldname='image']").find('.attached-file').hide();
         $("div[data-fieldname='image']").find('.img-container').next().hide();
     }
     get_attribute_images(optionId, doctype)
     get_attribute_videos(optionId)
 }

function get_attribute_images(optionId, doctype){
   if(optionId && doctype){
    frappe.call({
        method: 'go1_commerce.go1_commerce.v2.product.get_file_uploaded_imagelist',
        args: {
            child_name: optionId,
            child_doctype: doctype,
        },
        callback: function(data) {
             if(data.message.length < 12){
            var img_html = '<div class="row" id="img-gallery" style="max-height: 140px;">'
           }
           else{
              var img_html = '<div class="row" id="img-gallery" style="max-height: 140px; overflow-y:scroll;">'
           }
           $.each(data.message, function(i, v) {
             let checked = "";
                    img_html += `<div id="div${v.idx}" title="${v.name}" class="sortable-div div_${v.name}">
                        <div class="col-md-3" id="drag${v.name}">
                            <div style="position: relative; height: 60px;width:60px;margin-bottom: 10px;" class="">
                                <img class="img-name" src="${v.thumbnail}" title="${v.title}" id="${v.name1}" style="position: absolute;">
                            </div>
                        </div>
                    </div>`;
           })
           img_html += '</div>';
           
           
           setTimeout(() =>{
                $("div[data-fieldname='attribute_image_html']").html(img_html)
           },100)
        
        }
    })
    }
}
function get_attribute_videos(optionId, doctype){
    if(optionId){
     frappe.call({
        method: 'go1_commerce.go1_commerce.doctype.product.product.get_attribute_option_videos',
        args: {
            option_id: optionId
        },
        callback: function(data) {
            var html = '<table class="table table-bordered" id="OptionsData1"><thead style="background: #F7FAFC;"><tr><th width="65%">Video URL</th><th>Type</th><th>Actions</th></tr></thead>';
           if (data.message != undefined) {
                    $.each(data.message, function(i, d) {
                        
                        
                        html +='<tr id="tr-' + d.name +'"><td><i class="fa fa-file-video-o" aria-hidden="true"></i><span style="padding-left: 5px;">'+d.youtube_video_id +'</span></td><td>'+d.video_type+'</td>';

                        html += ' <td>'
                        
                            
                        
                        html+='<a class="btn btn-xs btn-danger" style="margin-left:10px;" onclick=DeleteAttributeOptionVideo("' + d.name + '","' + d.option_id + '")>Delete</a></td></tr>';
                    });
                }
                else {
                    html += '<tr><td colspan="6" align="center">No Records Found.</td></tr>';
                }
            html += '</tbody>';
                html += '</table>';
           $("div[data-fieldname='attribute_video']").html(html)
        }
    })
    }else{
        var html = '<table class="table table-bordered" id="OptionsData1"><thead style="background: #F7FAFC;"><tr><th width="65%">Video URL</th><th>Type</th><th>Actions</th></tr></thead>';
        html += '<tr><td colspan="6" align="center">No Records Found.</td></tr>';
        html += '</tbody>';
        html += '</table>';
        $("div[data-fieldname='attribute_video']").html(html)
    }
}
function DeleteAttributeOption(optionId) {
    if(cur_frm.doc.variant_combination.length > 0){
        var variant_combination = cur_frm.doc.variant_combination;
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.delete_attribute_option_alert',
            args: {
                option: optionId
            },
            callback: function(data) {
                if(data.message == "Success"){
                    deleteAttr(optionId)
                }
            }
        })
    }else{
        deleteAttr(optionId)
    }
}
function deleteAttr(optionId){
    var result = confirm("Are you sure want to delete?");
    if (result) {
        frappe.call({
            method: 'go1_commerce.go1_commerce.doctype.product.product.delete_product_attribute_option',
            args: {
                option: optionId
            },
            callback: function(data) {
                if (data.message.status == 'success') {
                    let length = $('div[data-fieldname="ht"] tbody tr').length;
                    if (length == 1) {
                        $('div[data-fieldname="ht"] tbody').html('<tr><td colspan="5" align="center">No Records Found.</td></tr>')
                    } else {
                        $('div[data-fieldname="ht"] tbody tr[id="tr-' + optionId + '"]').remove();
                    }
                }
            }
        })
    }
}

function EditAttributeOptions(optionId, doctype) {

      var field1 = cur_dialog.get_field("sec1")
        field1.df.hidden = 0;
        field1.refresh();

         var field2 = cur_dialog.get_field("sec01")
        field2.df.hidden = 0;
        field2.refresh();
if(cur_frm.catalog_settings.enable_product_video){
         var field3 = cur_dialog.get_field("sec02")
        field3.df.hidden = 0;
        field3.refresh();
      }

           var field4 = cur_dialog.get_field("sec000")
                field4.df.hidden = 0;
                field4.refresh();


   if(!doctype){
       doctype = "Product Attribute Option"
   }
    
    
    
    $("#hdnSelectedDoc").val();

    $("input[data-fieldname='option_value']").val($("#tr-" + optionId).find("td:eq(0)").text());
    $("input[data-fieldname='display_order_no']").val($("#tr-" + optionId).find("td:eq(1)").text());
    $("input[data-fieldname='price_adjustment']").val($("#tr-" + optionId).find("td:eq(2)").text());
    $("input[data-fieldname='weight_adjustment']").val($("#tr-" + optionId).find("td:eq(3)").text());
    $("input[data-fieldname='parent_option']").val($("#tr-" + optionId).find("td:eq(4)").text());

    /*$("input[data-fieldname='is_pre_selected']").val($("#tr-" + optionId).find("td:eq(4)").text());*/
    if($("#tr-" + optionId).find("td:eq(4)").text() == '-'){
        $("input[data-fieldname='attribute_color']").val('');
    }
    else{
        var color = 'background:'+$("#tr-" + optionId).find("td:eq(4)").text();
        $("input[data-fieldname='attribute_color']").val($("#tr-" + optionId).find("td:eq(4)").text());
        $("input[data-fieldname='attribute_color']").attr('style',color);
    }
    
    

    if($("#tr-" + optionId).find("td#disable").text() =="1"){
        $("input[data-fieldname='disable']").prop("checked", true);

         $("div[data-fieldname='available_html']").removeClass('hide-control');

         $("div[data-fieldname='available_html']").find('input[data-fieldname="available_datetime"]').show();

    }
    else{
        $("#tr-" + optionId).find("td#disable").prop("checked", false)
    }
    $("div[data-fieldname='available_html']").find('input[data-fieldname="available_datetime"]').val($("#tr-" + optionId).find("td#date_time").text());

    if($("#tr-" + optionId).find("td:eq(5)").text() == "1"){

        $('input[data-fieldname = is_pre_selected').prop("checked", true)
    }else{
        $('input[data-fieldname = is_pre_selected').prop("checked", false)
    }
    
    if($("#tr-" + optionId).find("td:eq(6)").text() == '-'){
        $("input[data-fieldname='product_title']").val('');
    }
    else{
        $("input[data-fieldname='product_title']").val($("#tr-" + optionId).find("td:eq(6)").text());
    }
      let image = $("#tr-" + optionId).attr('data-image');
    $("#hdnAttributeOptionid").val(optionId);
    if (image != undefined && image != null && image != 'null' && image != 0 && image != "") {
        let html = '<img class="img-responsive attach-image-display" src="' + image + '" /><div class="img-overlay">\
        <span class="overlay-text">Change</span></div>';
        $("div[data-fieldname='image']").find('.missing-image').hide();
        $("div[data-fieldname='image']").find('.img-container').show();
        $("div[data-fieldname='image']").find('.img-container').next().show();
        $("div[data-fieldname='image']").find('.img-container').html(html)
        $("div[data-fieldname='image']").find('.attached-file').show();
        $('div[data-fieldname="image"]').find('.attached-file-link').text('');
        $("div[data-fieldname='image']").find('.attached-file-link').text(image)
    }
    else{
        $('div[data-fieldname="image"]').find('.attached-file-link').text('')
        $('div[data-fieldname="image"]').find('.img-container').find('img').attr('src','');
        $("div[data-fieldname='image']").find('.missing-image').show();
        $("div[data-fieldname='image']").find('.img-container').hide();
        $("div[data-fieldname='image']").find('.attached-file').hide();
        $("div[data-fieldname='image']").find('.img-container').next().hide();
    }
    get_attribute_images(optionId, doctype)
    get_attribute_videos(optionId)
}
