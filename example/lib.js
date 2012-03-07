function parse_fieldsets(element){
    var obj = {};
    $(element).children(":not(a, legend, label, span, .ignore, input[type=submit], input[type=radio]:not(:checked), p)").each(function(){
        var tag = $(this)[0].tagName.toLowerCase();
        if(tag != 'fieldset' && tag != 'form' && tag != 'p'){
            try{
            	var name = $(this).attr('name');
                if(!val){
                    var tit = $(this).attr('placeholder');
                	var val = $(this).val();
                }
                if(tit != val && val != 'None'){
                    obj[name] = val
                }else{
                    obj[name] = null
                }
            }catch(e){
                console.log(e);
            }
        }else if(tag == 'fieldset'){
            var id = $(this).attr('name');
            res = parse_fieldsets(this);
            for(i in res){
                obj[i] = res[i]
            }
        }
        //tos check
        if ($(this)[0].type == 'checkbox'){
            obj[name] = ($(this).context.checked) ? 'on' : '';
        }
    });
    return obj
}

function forms(){
    $("form").each(function(){
        console.log(this);
        if(!this.set_submit){
            this.set_submit = true;
            $(this).submit(function(){
                console.log(this);
                try{
                    var data = {};
                    $("#error").html("creating account");
                    $("#error").show("blind");
                    try{
                        data.form = JSON.stringify(parse_fieldsets(this));
                        console.log(data.form)
                    }catch(e){
                        console.log(e);
                    }
                    var self = this;
                    var action = $(this).attr("action") ? $(this).attr("action") : '/';
                    $.ajax({
                        url: action,
                        data:data, 
                        success:function(res){
                            if(res.success){
                                $("#error").html("SUCCESS: " + res.data);
                                $("#error").show("blind");
                            }else{
                                st = "<ul>";
                                for(i in res.data){
                                    st+= "<li>"+i+": "+res.data[i]+"</li>";
                                }
                                st+="</ul>";
                                $("#error").html("Error: " + st);
                                $("#error").show("blind");
                            }
                            $("#form1").html(res.html);
                            $("input[type=submit]").removeAttr("disabled");
                            forms();
                        },
                        error:function(a,b,c){
                            self.submitting = false;
                            console.log(a);
                            console.log(b);
                            console.log(c);
                        },
                        timeout: 100000,
                        dataType:'json',
                        type: "POST"
                    });
                    return false;
                }catch(e){
                    console.log(e);
                }
            });
        }
    })
}