function display_c()
{
var refresh = 1000;
mytime = setTimeout('display_ct()', refresh)
}

function display_ct()
{
var x = new Date()
var hour = x.getHours();
var minute = x.getMinutes();

if (minute < 10 )
{
    minute = '0' + minute;
}

var x1 = + ' ' +  hour + ':' + minute;

document.getElementById('ct').innerHTML = x1
display_c();
}
