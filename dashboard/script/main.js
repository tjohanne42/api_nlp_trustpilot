$(document).ready(function() {
    $("#search-box-company").keyup(function() {
        $("#search-box-company").css("background", "#FFF url(loaderIcon.gif) no-repeat 165px");
        if ($(this).val().length > 2) {
            $.ajax({
                type: "GET",
                url: "http://127.0.0.1:8000/api/v1/company/query/" + $(this).val(),
                //data: 'name=' + $(this).val(), // POST
                success: function(data) {
                    let companies = JSON.parse(data);
                    let lines = "<ul id='company-list'>";
                    for (var i = 0; i < Object.keys(companies).length; i++) {
                        var companyKey = Object.keys(companies)[i];
                        var companyName = Object.values(companies)[i];
                        lines += "<li onClick=\"selectCompany('" + companyKey + "')\">" + companyName + "</li>";
                    }
                    lines += "</ul>";
                    $("#suggestion-box-company").show();
                    $("#suggestion-box-company").html(lines);
                    $("#search-box-company").css("background", "#FFF");
                }
            });
        } else {
            //On efface les champs
            $("#suggestion-box-company").hide();
            $("#company-category").text("");
            $("#company-link").attr("href", "");
            $("#company-link").text("");
        }
    }).focusout(function() {
        setTimeout(function() {
            $("#suggestion-box-company").hide();
        }, 500);
    }).focusin(function() {
            $("#suggestion-box-company").show();
    });

/*
    let increment = true;
    let valeur = 0;
    setInterval(function() {
        if (valeur == 100) {
            increment = false
        }
        else if (valeur == 0) {
            increment = true;
        };
        if (increment == true) {
            valeur++
        }
        else {
            valeur--
        };
        $('.progress-bar').css('width', valeur+'%').attr('aria-valuenow', valeur);
    }, 500);
*/

    setInterval(function() {
        $.ajax({
            type: "GET",
            url: "http://127.0.0.1:8000/api/v1/get_status",
            success: function(data) {
                let status = JSON.parse(data);
                $('.progress-bar').css('width', status+'%').attr('aria-valuenow', status);
            }
        })
    }, 500);

    $("#search-box-category").keyup(function() {
        $("#search-box-category").css("background", "#FFF url(loaderIcon.gif) no-repeat 165px");
        if ($(this).val().length > 2) {
            $.ajax({
                type: "GET",
                url: "http://127.0.0.1:8000/api/v1/category/query/" + $(this).val(),
                //data: 'name=' + $(this).val(), // POST
                success: function(data) {
                    let categories = JSON.parse(data);
                    let lines = "<ul id='category-list'>";
                    for (var i = 0; i < Object.keys(categories).length; i++) {
                        var categoryKey = Object.keys(categories)[i];
                        var categoryName = Object.values(categories)[i];
                        lines += "<li onClick=\"selectCategory('" + categoryKey + "')\">" + categoryName + "</li>";
                    }
                    lines += "</ul>";
                    $("#suggestion-box-category").show();
                    $("#suggestion-box-category").html(lines);
                    $("#search-box-category").css("background", "#FFF");
                }
            });
        } else {
            //On efface les champs
            //$("#suggestion-box-category").hide();
            $("#category-level").text("");
            $("#category-link").attr("href", "");
            $("#category-link").text("");
        }
    }).focusout(function() {
        setTimeout(function() {
            //$("#suggestion-box-category").hide();
        }, 500);
    });
});

function selectCompany(key) {
    $.ajax({
        type: "GET",
        url: "http://127.0.0.1:8000/api/v1/company/" + key,
        //data: 'name=' + $(this).val(), // POST
        success: function(data) {
            var companyName = data.name;
            var companyCategory = data.category;
            var companyLink = data.link;
            $("#search-box-company").val(companyName);
            $("#company-category").text(companyCategory);
            $("#company-link").attr("href", companyLink);
            $("#company-link").text(companyLink);
            //$("#suggestion-box-company").hide();
        }
    });
}

function selectCategory(key) {
    $.ajax({
        type: "GET",
        url: "http://127.0.0.1:8000/api/v1/category/" + key,
        //data: 'name=' + $(this).val(), // POST
        success: function(data) {
            var categoryName = data.name;
            var categoryLevel = data.level;
            var categoryLink = data.link;
            $("#search-box-category").val(categoryName);
            $("#category-level").text(categoryLevel);
            $("#category-link").attr("href", categoryLink);
            $("#category-link").text(categoryLink);
            $("#suggestion-box-category").hide();
        }
    });
}