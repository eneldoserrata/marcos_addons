jQuery(window).load(function () {
    var strVar = "";
    strVar += "<li>";
    strVar += "                <button onclick=\"TogetherJS(this); return false;\">Start TogetherJS<\/button>";
    strVar += "            <\/li>";
    $(".oe_systray").append(strVar)
});
