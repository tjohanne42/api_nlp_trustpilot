$(document).ready(function() {
    if (categoryKey == -1) {
        $('#btn-Launch-category').prop("disabled", true);
        $("#search-box-category").val(categoryName);
        $("#search-box-company").val(companyName);
    }

    //Navbar events
    $(".nav-item .nav-link").on("click", function() {
        disableActiveNavBar()
        let navbarClicked = $(this).attr("data-target");
        enableNavBar(navbarClicked);
    });

    function disableActiveNavBar() {
        let navActive = $(".nav-item").find(".active");
        navActiveid = navActive.attr("data-target");
        navActive.removeClass("active"); //Disable link
        $("#" + navActiveid).addClass("d-none"); //Hide div
        console.log("disabled " + navActiveid);
        return navActiveid;
    }

    function enableNavBar(navBarToShow) {
        $('*[data-target="' + navBarToShow + '"]').addClass("active"); //Enable new link        
        $("#" + navBarToShow).addClass("active"); //Enable new link        
        console.log("active " + navBarToShow);
        if (navBarToShow == "main-dashboard") {
            $("#" + navBarToShow).removeClass("d-none");
        } else if (navBarToShow == "main-companies") {
            $("#" + navBarToShow).removeClass("d-none");
        } else if (navBarToShow == "main-categories") {
            $("#" + navBarToShow).removeClass("d-none");
        }
    }

    //Pour afficher la bonne section au démarrage défini dans l'URL
    var pageURL = $(location).attr("href");
    var params = pageURL.split("#").pop();
    console.log(params)
    disableActiveNavBar()
    enableNavBar(params)

    $("#search-box-company").keyup(function() {
        $("#search-box-company").css("background", "#FFF no-repeat 165px");
        if ($(this).val().length > 2) {
            $.ajax({
                type: "GET",
                url: "http://127.0.0.1:8000/api/v1/company/query/" + $(this).val(),
                //data: 'name=' + $(this).val(), // POST
                success: function(data) {
                    console.log(data);
                    let companies = JSON.parse(data);
                    let lines = "<ul class='suggestion-list'>";
                    for (var i = 0; i < Object.keys(companies).length; i++) {
                        var key = Object.keys(companies)[i];
                        var name = Object.values(companies)[i];
                        lines += "<li onClick=\"selectCompany('" + key + "')\">" + name + "</li>";
                    }
                    lines += "</ul>";
                    $("#suggestion-box-company").show();
                    $("#suggestion-box-company").html(lines);
                    $("#search-box-company").css("background", "#FFF");
                }
            });
        } else {
            //On efface les champs
            $("#suggestion-box-company").hide(500);
            $("#company-link").attr("href", "");
            $("#company-link").text("");
            $("#company-form").addClass("d-none");
        }
    }).focusout(function() {
        setTimeout(function() {
            $("#suggestion-box-company").hide(500);
        }, 500);
    });

    $("#search-box-category").keyup(function() {
        $("#search-box-category").css("background", "#FFF no-repeat 165px");
        if ($(this).val().length > 2) {
            $.ajax({
                type: "GET",
                url: "http://127.0.0.1:8000/api/v1/category/query/" + $(this).val(),
                //data: 'name=' + $(this).val(), // POST
                success: function(data) {
                    console.log(data);
                    let categories = JSON.parse(data);
                    let lines = "<ul class='suggestion-list'>";
                    for (var i = 0; i < Object.keys(categories).length; i++) {
                        var key = Object.keys(categories)[i];
                        var name = Object.values(categories)[i];
                        lines += "<li onClick=\"selectCategory('" + key + "')\">" + name + "</li>";
                    }
                    lines += "</ul>";
                    $("#suggestion-box-category").show();
                    $("#suggestion-box-category").html(lines);
                    $("#search-box-category").css("background", "#FFF");
                }
            });
        } else {
            //On efface les champs
            $("#suggestion-box-category").hide(500);
            $("#category-link").attr("href", "");
            $("#category-link").text("");
            $('#btn-Launch-category').prop("disabled", true);
        }
    }).focusout(function() {
        setTimeout(function() {
            $("#suggestion-box-category").hide(500);
        }, 500);
    });

    $('#btn-Launch-category').on('click', function(event) {
        event.preventDefault(); // To prevent following the link (optional)
        if (categoryName == "")
            categoryName = $("#search-box-category").val();
        if (categoryKey > -1) {
            $.ajax({
                type: "GET",
                url: "http://127.0.0.1:8000/api/v1/dashboard/summary/category/" + categoryKey,
                //data: 'name=' + $(this).val(), // POST
                success: function(data) {
                    uid = data.uid;
                    console.log(data);
                    //Save uid
                    disableActiveNavBar()
                    enableNavBar("main-dashboard")
                    $("#main-summary").addClass("d-none");
                }
            });
        }
    });

    let uid = ""
    let waitResult = false;
    setInterval(function() {
        if (uid != "") {
            if (!waitResult) {
                waitResult = true; // On empêche les doubles requêtes
                $.ajax({
                    type: "GET",
                    url: "http://127.0.0.1:8000/api/v1/dashboard/summary/status/" + uid,
                    //data: 'name=' + $(this).val(), // POST
                    success: function(data) {
                        let result = data.result;
                        if (data.status == 'complete') {
                            uid = "";
                            console.log("Task finished!", result);
                            $("#main-summary").removeClass("d-none");
                            $('#category-name-text').text(categoryName);
                            $('#category-stars-text').text("(" + result.stars_mean.toFixed(1));
                            $("#summary-star1").removeClass("fa-star");
                            $("#summary-star2").removeClass("fa-star");
                            $("#summary-star3").removeClass("fa-star");
                            $("#summary-star4").removeClass("fa-star");
                            $("#summary-star5").removeClass("fa-star");
                            $("#summary-star1").removeClass("fa-star-o");
                            $("#summary-star2").removeClass("fa-star-o");
                            $("#summary-star3").removeClass("fa-star-o");
                            $("#summary-star4").removeClass("fa-star-o");
                            $("#summary-star5").removeClass("fa-star-o");
                            if (result.stars_mean < 1) {
                                $("#summary-star1").addClass("fa-star-o");
                                $("#summary-star2").addClass("fa-star-o");
                                $("#summary-star3").addClass("fa-star-o");
                                $("#summary-star4").addClass("fa-star-o");
                                $("#summary-star5").addClass("fa-star-o");
                            } else if (result.stars_mean < 2) {
                                $("#summary-star1").addClass("fa-star");
                                $("#summary-star2").addClass("fa-star-o");
                                $("#summary-star3").addClass("fa-star-o");
                                $("#summary-star4").addClass("fa-star-o");
                                $("#summary-star5").addClass("fa-star-o");
                            } else if (result.stars_mean < 3) {
                                $("#summary-star1").addClass("fa-star");
                                $("#summary-star2").addClass("fa-star");
                                $("#summary-star3").addClass("fa-star-o");
                                $("#summary-star4").addClass("fa-star-o");
                                $("#summary-star5").addClass("fa-star-o");
                            } else if (result.stars_mean < 4) {
                                $("#summary-star1").addClass("fa-star");
                                $("#summary-star2").addClass("fa-star");
                                $("#summary-star3").addClass("fa-star");
                                $("#summary-star4").addClass("fa-star-o");
                                $("#summary-star5").addClass("fa-star-o");
                            } else if (result.stars_mean < 5) {
                                $("#summary-star1").addClass("fa-star");
                                $("#summary-star2").addClass("fa-star");
                                $("#summary-star3").addClass("fa-star");
                                $("#summary-star4").addClass("fa-star");
                                $("#summary-star5").addClass("fa-star-o");
                            } else {
                                $("#summary-star1").addClass("fa-star");
                                $("#summary-star2").addClass("fa-star");
                                $("#summary-star3").addClass("fa-star");
                                $("#summary-star4").addClass("fa-star");
                                $("#summary-star5").addClass("fa-star");
                            }
                            $('#category-nb-companies-text').text(result.nb_companies + " compagnies");
                            $('#category-review-count-text').text(result.nb_reviews + " commentaires");
                            let wordcloud = result.wordcloud;
                            //$('#current-task').addClass("d-none");
                            $('#status-task').text("Terminé");
                            $('.progress-bar').css('width', '100%').attr('aria-valuenow', 100);

                            //Lancement de thread pour les wordcloud sinon l'un d'eux risque d'être vide
                            setTimeout(function() { draw_wordcloud("canvas-wcloud-pos", wordcloud, true); }, 0);
                            setTimeout(function() { draw_wordcloud("canvas-wcloud-neg", wordcloud, false); }, 0);

                            //draw_wordcloud("canvas-wcloud-neg", wordcloud, false);
                            //draw_wordcloud("canvas-wcloud-pos", wordcloud, true);
                            draw_chart_pie(result.repartition_sentiment);
                            draw_chart_stars_evolution(result.stars_evolution_by_month)
                            draw_chart_sentiment_evolution(result.sentiment_evolution_by_month)
                        } else {
                            let valeur = ((data.progress * 100) / data.progress_max).toFixed(0);
                            //$('#current-task').removeClass("d-none");
                            $('#status-task').text(data.label + " en cours... (" + valeur + "%)");
                            $('.progress-bar').css('width', valeur + '%').attr('aria-valuenow', valeur);
                        }
                        waitResult = false;
                    },
                    error: function(xhr, status, error) {
                        uid = "";
                        //$('#current-task').addClass("d-none");
                        $('#status-task').text("Erreur !")
                        $('.progress-bar').css('width', '0%').attr('aria-valuenow', 0);
                        console.log("Task finished with error!", xhr, status, error);
                        waitResult = false;
                    }
                });
            }
        }
    }, 500);

});

var companyKey = 0;
var companyName = "";
var companyPhone = "";
var companyLocation = "";
var companyCategory = "";
var companyStars = "";
var companyReviewCount = "";
var companyLogo = "";
var companyMail = "";
var companyLink = "";
var companyUrl = "";

function selectCompany(key) {
    $.ajax({
        type: "GET",
        url: "http://127.0.0.1:8000/api/v1/company/" + key,
        //data: 'name=' + $(this).val(), // POST
        success: function(data) {
            companyKey = key;
            companyName = data.name;
            companyCategory = data.category;
            companyPhone = data.phone;
            companyLocation = data.location;
            companyStars = data.stars.toFixed(1);
            companyReviewCount = data.review_count;
            companyLogo = data.logo;
            companyMail = data.mail;
            companyLink = data.link;
            companyUrl = data.url;
            companyMail = companyMail.replaceAll(",", "<br>");
            $("#search-box-company").val(companyName);
            if (companyUrl != "") {
                $("#company-link").attr("href", companyUrl);
            } else {
                $("#company-link").attr("href", companyLink);
            }
            // On efface le précédent logo car il peut y avoir un temps de chargement du prochain
            $("#company-logo").attr("src", "img/photo.jpg");
            console.log('selectCompany:', companyLogo);
            if (companyLogo !== 'Inconnu') {
                $("#company-logo").attr("src", companyLogo);
            }
            $("#company-name-text").text(companyName);
            $("#company-category-text").text(companyCategory);
            $("#company-location-text").text(companyLocation);
            $("#company-phone-text").text(companyPhone);
            $("#company-mail-text").html(companyMail);
            $("#company-stars-text").text(companyStars);
            $("#company-review-count-text").text(companyReviewCount + " commentaires");
            $("#company-star1").removeClass("fa-star");
            $("#company-star2").removeClass("fa-star");
            $("#company-star3").removeClass("fa-star");
            $("#company-star4").removeClass("fa-star");
            $("#company-star5").removeClass("fa-star");
            $("#company-star1").removeClass("fa-star-o");
            $("#company-star2").removeClass("fa-star-o");
            $("#company-star3").removeClass("fa-star-o");
            $("#company-star4").removeClass("fa-star-o");
            $("#company-star5").removeClass("fa-star-o");
            if (companyStars < 1) {
                $("#company-star1").addClass("fa-star-o");
                $("#company-star2").addClass("fa-star-o");
                $("#company-star3").addClass("fa-star-o");
                $("#company-star4").addClass("fa-star-o");
                $("#company-star5").addClass("fa-star-o");
            } else if (companyStars < 2) {
                $("#company-star1").addClass("fa-star");
                $("#company-star2").addClass("fa-star-o");
                $("#company-star3").addClass("fa-star-o");
                $("#company-star4").addClass("fa-star-o");
                $("#company-star5").addClass("fa-star-o");
            } else if (companyStars < 3) {
                $("#company-star1").addClass("fa-star");
                $("#company-star2").addClass("fa-star");
                $("#company-star3").addClass("fa-star-o");
                $("#company-star4").addClass("fa-star-o");
                $("#company-star5").addClass("fa-star-o");
            } else if (companyStars < 4) {
                $("#company-star1").addClass("fa-star");
                $("#company-star2").addClass("fa-star");
                $("#company-star3").addClass("fa-star");
                $("#company-star4").addClass("fa-star-o");
                $("#company-star5").addClass("fa-star-o");
            } else if (companyStars < 5) {
                $("#company-star1").addClass("fa-star");
                $("#company-star2").addClass("fa-star");
                $("#company-star3").addClass("fa-star");
                $("#company-star4").addClass("fa-star");
                $("#company-star5").addClass("fa-star-o");
            } else {
                $("#company-star1").addClass("fa-star");
                $("#company-star2").addClass("fa-star");
                $("#company-star3").addClass("fa-star");
                $("#company-star4").addClass("fa-star");
                $("#company-star5").addClass("fa-star");
            }
            $("#suggestion-box-company").hide(500);
            $("#company-form").removeClass("d-none");
        }
    });
}

var categoryKey = -1;
var categoryName = "";
var categoryLevel = 0;
var categoryLink = "";

function selectCategory(key) {
    $.ajax({
        type: "GET",
        url: "http://127.0.0.1:8000/api/v1/category/" + key,
        //data: 'name=' + $(this).val(), // POST
        success: function(data) {
            categoryKey = key;
            categoryName = data.name;
            categoryLevel = data.level;
            categoryLink = data.link;
            $("#search-box-category").val(categoryName);
            var category_link = categoryLink.split("/")
            $("#category-link").attr("href", "https://fr.trustpilot.com/categories/" + category_link[category_link.length - 1]);
            $("#category-link").text("Visiter la page...");
            $("#suggestion-box-category").hide(500);
            $('#btn-Launch-category').prop("disabled", false);
        }
    });
}

function scaleBetween(unscaledNum, minAllowed, maxAllowed, min, max) {
    return (maxAllowed - minAllowed) * (unscaledNum - min) / (max - min) + minAllowed;
}

function draw_wordcloud(canvasName, wordlist, positive = None) {

    var list;
    if (positive == true) {
        list = wordlist.pos;
    } else if (positive == false) {
        list = wordlist.neg;
    }

    if (list.count.length > 0) {
        var maxValuePos = wordlist.pos.count.max();
        var maxValueNeg = wordlist.neg.count.max();
        var minValuePos = wordlist.pos.count.min();
        var minValueNeg = wordlist.neg.count.min();

        var maxValue = 0;
        var minValue = 0;
        if (positive == true) {
            $("#mask-wcloud-pos").addClass("d-none");
            maxValue = maxValuePos;
            minValue = minValuePos;
        } else if (positive == false) {
            $("#mask-wcloud-neg").addClass("d-none");
            maxValue = maxValueNeg;
            minValue = minValueNeg;
        }
    }

    var pixelWidth = 400;
    var pixelHeight = 300;

    $("#" + canvasName).attr('width', pixelWidth);
    $("#" + canvasName).attr('height', pixelHeight);

    // Set the options object
    var options = {};

    var optionslist = [];
    var listTest = [];
    var wordSizeMax = 50;
    var wordSizeMin = 20;
    console.log('wordSizeMax=' + wordSizeMax, ', wordSizeMin=' + wordSizeMin, 'maxValue=' + maxValue, ', minValue=' + minValue);
    if (list.count.length > 0) {
        for (let i = 0; i < list.count.length; i++) {
            var size = wordSizeMin + ((list.count[i] - minValue) * ((wordSizeMax - wordSizeMin) / (maxValue - minValue)));
            optionslist.push([list.words[i], Math.floor(size)]);
            listTest.push([list.words[i], list.count[i], Math.floor(size)]);
        }
        console.log(listTest)
    } else {
        //Pas de mots
        optionslist.push(['Aucun mot', wordSizeMin]);
    }

    options.list = optionslist;
    options.minRotation = 0;
    options.maxRotation = 0;
    if (positive == true)
        options.color = 'random-green';
    else if (positive == false)
        options.color = 'random-red';

    // All set, call the WordCloud()
    // Order matters here because the HTML canvas might by
    // set to display: none.
    WordCloud(canvasName, options);
}

function draw_chart_pie(sentiments) {
    data = {
        datasets: [{
            data: [sentiments.pos, sentiments.neg],
            backgroundColor: [
                'rgb(51, 230, 51)',
                'rgb(255, 92, 92)',
            ],
        }],
        // These labels appear in the legend and in the tooltips when hovering different arcs
        labels: [
            'Positif',
            'Négatif',
        ],
        colors: [
            'Green',
            'Red',
        ],
    };

    var ctx = document.getElementById('canvas-chart-pie').getContext('2d');
    // For a pie chart
    var myPieChart = new Chart(ctx, {
        type: 'pie',
        data: data,
        options: { aspectRatio: 1 }
    });
}

Array.prototype.max = function() {
    return Math.max.apply(null, this);
};
Array.prototype.min = function() {
    return Math.min.apply(null, this);
};

function draw_chart_stars_evolution(evolutions) {
    var list = [];
    var labels = [];
    for (var i = Object.keys(evolutions).length - 1; i >= 0; i--) {
        var key = Object.keys(evolutions)[i];
        var name = Object.values(evolutions)[i];
        var dict = {
            x: key,
            y: name
        };
        list.push(dict);
        labels.push(key);
    }

    var ctx = document.getElementById('canvas-stars-evolution').getContext('2d');
    ctx.canvas.width = 200;
    ctx.canvas.height = 100;
    var stackedLine = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Evolution des notations',
                backgroundColor: '#00BBF9',
                borderColor: '#00BBF9',
                data: list,
                fill: false,
            }],
        },
        options: {
            scales: {
                yAxes: [{
                    stacked: false
                }]
            }
        }
    });
}

function draw_chart_sentiment_evolution(sentiments) {
    var list = [];
    var labels = [];
    for (var i = Object.keys(sentiments).length - 1; i >= 0; i--) {
        var key = Object.keys(sentiments)[i];
        var name = Object.values(sentiments)[i];
        var dict = {
            x: key,
            y: name
        };
        list.push(dict);
        labels.push(key);
    }

    var ctx = document.getElementById('canvas-sentiments-evolution').getContext('2d');
    ctx.canvas.width = 200;
    ctx.canvas.height = 100;
    var stackedLine = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Evolution des sentiments',
                backgroundColor: '#9B5DE5',
                borderColor: '#9B5DE5',
                data: list,
                fill: false,
            }],
        },
        options: {
            scales: {
                yAxes: [{
                    stacked: false
                }]
            }
        }
    });
}

function sleep(seconds) {
    var waitUntil = new Date().getTime() + seconds * 1000;
    while (new Date().getTime() < waitUntil) true;
}