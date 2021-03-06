#!/usr/bin/perl -w

# written by andrewt@cse.unsw.edu.au September 2015
# as a starting point for COMP2041/9041 assignment 2
# http://cgi.cse.unsw.edu.au/~cs2041/assignments/bitter/

use CGI qw/:all/;
use CGI::Cookie;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use Mail::Sendmail;
use File::Copy;

%information = ();
sub main() {
    # print start of HTML ASAP to assist debugging if there is an error in the script
    print page_header();
    
    # Now tell CGI::Carp to embed any warning in HTML
    warningsToBrowser(1);

    # define some global variables
    $debug = 1;
    $dataset_size = "medium"; 
    $users_dir = "users";
    $bleats_dir = "bleats";

	%name_to_int={};
	my $i;
	for my $username (sort "$users_dir/*") {
		$username =~ s/.*\///;
		$name_to_int{$username} = $i;
		$i++;
	}

	
    %cookies = fetch CGI::Cookie;
    
    $logged_in = 0;
    
    $NUM_RESULTS = 16;
    $PAGE_INDEX = param('page_index') || 0;

    #logging out
    if (param('logout')) {
        print "<script>document.cookie='auth=0; path=/'</script>";
        %cookies = fetch CGI::Cookie;
        print_login();
    } else {
        if (defined $cookies{'auth'} && $cookies{'auth'}->value ne '0') { #logged in already
            $logged_in = 1;
            print_logout();
        } else {
            if (defined param('username') && defined param('password')) { #auth / logging in
                if (open my $userfile, "$users_dir/".param('username')."/details.txt") {
                    my $password_line = "";
                    for (<$userfile>) {
                        if (/^password:/) {
                            $password_line = $_;
                            last;
                        }
                    }
                    (my $password = param('password'));
                    $password_line =~ s/^password: //; #remove start of line
                    $password =~ s/ //g;
                    chomp($password_line);
                    $password_line =~ s/ //g;
                    if ($password eq $password_line) {
                        print "<script>document.cookie='auth=".param('username')."; path=/'</script>";
			            param('n', $name_to_int{param('username')}); #gets the number associated with the username
                        print_logout();
                        $logged_in = 1;
                        %cookies = fetch CGI::Cookie;
                    } else {
                        print_login();
                        print "Wrong Password\n";
                    }
                } else {
                    print_login();
                    print "User doesn't exist\n";
                }
            } else {
                print_login();
            }
        }
    }    
    
    %cookies = fetch CGI::Cookie;
    
   if(defined param('post_write')&& param('post_write') eq "True"){
        post_write();
   }
    if (param('group') && param('sign_pass') eq param('confirm_pass')) {
    	send_account_confirm();
    } elsif (param('signup')) {
	    sign_up_screen();
        org_sign_up();
    }

    if ($logged_in) {
        buffer_details();
        if (param("Search")){
    	    search_bleats(param("Search"));
        }  elsif (defined param('formpage')){
            print post();
        } elsif (defined param('settings')){
            settings();
        } elsif ($information{'org'} eq "true"){
            print profile();
            show_comp();
        } else {
            print_feed();
        }
    }
    
    if (param('approve')) {
        approve(param('approve'));        
    } elsif (param('disapprove')) {
        disapprove(param('disapprove'));        
    }
    
    print page_trailer();
}

sub approve($) {
    $id = $_[0];
    for $complaint_file (sort(glob("$bleats_dir/*"))) {
        $complaint_file =~ s/.*\///;
        if ($complaint_file eq $id) {
            open(F, "$bleats_dir/$complaint_file") or die;
            @list;
            for $line (<F>) {
                push @list, $line;
            }
            close F;
            open(F, ">", "$bleats_dir/$complaint_file") or die;
            for $line (@list) {

                if ($line =~ /^rep: (.*)/) {
                    $rep = $1;
                    $rep++;
                    $line = "rep: ".$rep;
                }
                                
                print F $line;
            }
            close F;
        }
    }
}

sub disapprove($) {
    $id = $_[0];
    for $complaint_file (sort(glob("$bleats_dir/*"))) {
        $complaint_file =~ s/.*\///;
        if ($complaint_file eq $id) {
            open(F, "$bleats_dir/$complaint_file") or die;
            @list;
            for $line (<F>) {
                push @list, $line;
            }
            close F;
            open(F, ">", "$bleats_dir/$complaint_file") or die;
            for $line (@list) {

                if ($line =~ /^rep: (.*)/) {
                    $rep = $1;
                    $rep--;
                    $line = "rep: ".$rep;
                }
                                
                print F $line;
            }
            close F;
        }
    }
}

#---------------------------------------------------#
# ACCOUNT RELATED FUNCTIONS                                       #
#---------------------------------------------------#
#buffer the information hash
sub buffer_details(){
    %cookies = fetch CGI::Cookie;

    my $username = $cookies{'auth'}->value;
    if ($username eq '0') {
        return;
    }
    my $details_filename = "./$users_dir/$username/details.txt";
    open my $p, "$details_filename" or die "can not open $details_filename: $!";
    while (my $line = <$p>){
        chomp $line;
        #if ($line =~ /^listens: (.*)/){
        #    @listens = split(' ',$1);
        #    #$information{"listens"}= \@listens;
        #}els
        if($line =~ /([^:]+): (.*)/){
            $information{"$1"}= "$2";
        }
    }
    close $p;
}

sub settings(){
    print "<div class=\"center\">";
    print "<h3> Change your details </h3><br><br>\n";
    print start_form, "\n";

    print "New password:\n", password_field(-name=>'newpwd',
                                            -class => 'form-control',
                                            -override=>1,
                                            -pattern=>"[A-Za-z0-9_\-]+",
                                            -maxlength=>30), "<br>\n";
    print "New email:\n", textfield(-name=>'email',
                                            -class => 'form-control',), "<br>\n";
    print "Enter current password:\n", password_field(-name=>'oldpwd',
                                                    -class => 'form-control',
                                                      -override=>1,
                                                      -pattern=>"[A-Za-z0-9_\-]+",
                                                      -maxlength=>30), "<br>\n";
    print hidden('username',"$username"),"\n";
    print hidden('loggedin',"$loggedIn"),"\n";
    print submit('imptsettings','Change'), "\n";
    print end_form, "<br>\n";

    print start_form, "\n";
    print "Full Name: \n", textfield(-name=>'name',
                                     -class => 'form-control',
                                     -default => $information{'full_name'},
                                     -maxlength=>30), "\n<br>";
    print "Home Latitude:\n", textfield(-name=>'latitude', 
                                        -class => 'form-control',
                                        -pattern=>"[0-9\.\-]+",
                                        -default => $information{'home_latitude'},
                                        -maxlength=>30), "\n<br>";
    
    print "Home Longitude:\n", textfield( -name=>'longitude', 
                                        -class => 'form-control',
                                         -default => $information{'home_longitude'},
                                         -pattern=>"[0-9\.\-]+",
                                         -maxlength=>30), "\n<br>";
   
    print "Profile description:<br>\n", textarea(-name=>'about',
                                                -class => 'form-control',
                                                  -default=>$information{'about'},
                                                  -rows=>3,
                                                  -columns=>60,
                                                  -maxlength=>500),"\n<br>";
    print "Maximum length 500 characters, HTML formatting supported.<p>\n";
    print hidden('username',"$username"),"\n";
    print hidden('loggedin',"$loggedIn"),"\n";
    print submit('normalsettings','Edit'), "\n";
    print end_form, "<br>\n";

    print start_form, "\n";
    print hidden('username',"$username"),"\n";
    print hidden('loggedin',"$loggedIn"),"\n";
    print submit('suspendacc','Suspend Account'), "\n";
    print end_form, "<br>\n";

    print start_form, "\n";
    print hidden('username',"$username"),"\n";
    print hidden('loggedin',"$loggedIn"),"\n";
    print submit('deleteacc','Delete Account'), "\n";
    print end_form, "<br>\n";
    print "</div>";

}

sub print_login {
    #<input type="submit" value="Forgot Password" class="btn"> TODO add later
    if (defined param('confirm') && defined param('loggedAs')){
        my $confirmuser = param('loggedAs');
        move("./$users_dir/tmp/$confirmuser","./$users_dir/$confirmuser");
        print "Confirmation successful! Please login.\n";
    }
    print <<END_OF_HTML;
<p></p><p></p><p></p><p></p>
<div>
    <form method="POST" action="">
        <label>Username:</label>
        <input type="text" name="username">
        <label>Password:</label>
        <input type="password" name="password">
        <input type="submit" value="Login" class="btn btn-primary">
    </form>
    <form method="POST" action="">
        <input type="hidden" name="signup" value=1>
        <input type="submit" value="Sign-up" class="btn btn-success">
    </form>
</div>
END_OF_HTML
    $logged_in = 0;
}


#complete!
sub create_user_account {
	my $new_user = param('sign_user');
	my $new_pass = param('sign_pass');
	my $new_email = param('email');
	my $uniqId = param('uniqId');
        my $org = param('group');
        mkdir("./$users_dir/tmp/$new_user") or die "cannot make ./$users_dir/tmp/$new_user";
	open DETAILS, ">","./$users_dir/tmp/$new_user/details.txt" or die "cannot open ./$users_dir/tmp/$new_user/details.txt";
	print DETAILS "username: $new_user\n";
	print DETAILS "password: $new_pass\n";
	print DETAILS "email: $new_email\n";
	print DETAILS "idnum: $uniqId\n";
    print DETAILS "org: $org\n";
    print DETAILS "rep: 100";
	close DETAILS;
}

sub send_account_confirm {
	my $email = param('email');
	my $newusr = param('sign_user');

        #check if username exists
	if (-d "$users_dir/$newusr" || -d "$users_dir/tmp/$newusr") {
		print "Username is already taken";
		return;
	}
        create_user_account();

        $to = "$email";
        $url = "http://cgi.cse.unsw.edu.au/~z5019263/cgi-hackathon/bitter.cgi";
        $from = 'z5013079@zmail.unsw.edu.au';
        $subject = 'Welcome to Korform!';
        $message = "Your account has been created. Copy and paste the following url into your browser to confirm your registration:
    $url?loggedAs=$newusr&confirm=$to";
         
        open(MAIL, "|/usr/sbin/sendmail -t");
        print MAIL "To: $to\n";
        print MAIL "From: $from\n";
        print MAIL "Subject: $subject\n";
        print MAIL "Content-type:text/html\n";
        print MAIL $message;

	close(MAIL);
	print "<p></p>Account created! Please check your email to confirm.<p></p>\n";

}

sub org_sign_up{
    print <<eof;
    
    <h2> Register Your Organisation or Company</h2>  
    <p>Only alphanumeric  characters, underscores and dashes are allowed<p> for username and password, to a maximum of 30 characters.<p>
    <form method="POST" action="">
    <table cellspacing=10> 
        <tr>    
            <td> <label class="signup">Username:</label> </td>
            <td> <input type="text" name="sign_user" maxlength="30" pattern="[A-Za-z0-9_-]+"> </td>
        </tr>
        <tr>
            <td> <label class="signup">Company ID:</label> </td>
            <td> <input type="text" name="uniqId"> </td>
        </tr>
        <tr>
            <td> <label class="signup">Password:</label> </td>
            <td> <input type="password" name="sign_pass" maxlength="30" pattern="[A-Za-z0-9_-]+"> </td>
        </tr>
        <tr>
            <td> <label class="signup">Confirm Password:</label> </td>
            <td> <input type="password" name="confirm_pass" maxlength="30" pattern="[A-Za-z0-9_-]+"> </td>
        </tr>
        <tr>
            <td> <label class="signup">Email:</label> </td>
            <td> <input type="text" name="email" pattern="[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+[a-zA-Z0-9]"> </td>
        </tr>
        <tr>
        <input type="hidden" name="group" value="true">
        <input type="submit" value="Submit" class="btn">
        </tr>
    </table>
    </form> 

eof
}
sub sign_up_screen {
    print <<eof;
	
    <h2> Sign Up </h2>	
    <form method="POST" action="">
    <table cellspacing=10> 
        <tr>    
            <td> <label class="signup">Username:</label> </td>
            <td> <input type="text" name="sign_user" maxlength="30" pattern="[A-Za-z0-9_-]+"> </td>
        </tr>
        <tr>
            <td> <label class="signup">Indonesian ID:</label> </td>
            <td> <input type="text" name="uniqId" maxlength="16"> </td>
        </tr>
        <tr>
            <td> <label class="signup">Password:</label> </td>
            <td> <input type="password" name="sign_pass" maxlength="30" pattern="[A-Za-z0-9_-]+"> </td>
        </tr>
        <tr>
            <td> <label class="signup">Confirm Password:</label> </td>
            <td> <input type="password" name="confirm_pass" maxlength="30" pattern="[A-Za-z0-9_-]+"> </td>
        </tr>
        <tr>
            <td> <label class="signup">Email:</label> </td>
            <td> <input type="text" name="email" pattern="[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+.[a-zA-Z0-9-.]+[a-zA-Z0-9]"> </td>
        </tr>
        <tr>
        <input type="hidden" name="group" value="false">
        <input type="submit" value="Submit" class="btn">
        </tr>
    </table>
    </form>	

eof
}
#---------------------------------------------------#
# POST RELATED FUNCTIONS                                           #
#---------------------------------------------------#
sub upload_image {
    $CGI::POST_MAX = 1024 * 5000; #set max size to 5MB
    my $username = $cookies{'auth'}->value;
    my $filename = param('upload');
    my $upload_filehandle = upload("upload");

    my $upload_dir = "/upload";
    
    open ( UPLOADFILE, ">$users_dir/$username/profile.jpg" ) or die "$!";
    binmode UPLOADFILE;
    while ( <$upload_filehandle> ) {
        print UPLOADFILE;
    }

    close UPLOADFILE;
}

sub addremove_listener {
    my $username = $cookies{'auth'}->value;
    my $other_user = param('listen');
    
    open(my $in, '<', "$users_dir/$username/details.txt") or die; #opens file for read
    for (sort(glob("$users_dir/*"))) {
        if ($other_user == 0) { #found the correct user;
            ($other_user = $_) =~ s/.*\///; #extracts the username
            last;
        }
        $other_user--;
    }
    my @lines;
    my $add = 1;
    for (<$in>) {
        if (/^listen/) {
            if (/$other_user/) { #removing listen
                s/ $other_user//;
            } else { #adding listen
                s/$/ $other_user/;
            }
            
        }
        push @lines, $_;

    }
    
    open(my $out, '>', "$users_dir/$username/details.txt") or die; #opens file for write
    for (@lines) {
        print $out $_;
    }
    
}

sub send_message {
    
    my $message = $_[0];
    my @bleat_id = reverse (sort(glob("$bleats_dir/*"))); #last bleat index
    #$bleat_id[0];
    %cookies = fetch CGI::Cookie;
    $bleat_id[0] =~ s/.*\///; #get bleat id
    
    my $user_to_show = $cookies{'auth'}->value;
    my $details_filename = "$users_dir/$user_to_show/details.txt";
    

    open F, "$details_filename" or die "can not open $details_filename: $!";
    
    open BLEAT_FILE, '>'."$bleats_dir/".(int($bleat_id[0])+1) or die;
    
    for (<F>) {
        if (/(username|longitude|latitude):/) { #writes these details into the bleat
            print BLEAT_FILE $_;
        }
    }
    print BLEAT_FILE "bleat: $message\n";
    print BLEAT_FILE "time: ", time, "\n";
    if (param('bleat_reply')) {
        print BLEAT_FILE "in_reply_to: ".param('bleat_reply')."\n";
    }
    
    close BLEAT_FILE;
    
    open BLEAT_LIST, '>>'."$users_dir/$user_to_show/bleats.txt";
 
}

#---------------------------------------------------#
# SEARCH FUNCTIONS                                                  #
#---------------------------------------------------#

sub search_bleats($) {
    my $search_term = $_[0];
    my @bleat_id = reverse (sort(glob("$bleats_dir/*")));
    
    print "<h2> Search Results for ".$search_term." </h2>";
    my $bleat_index = 0;
    for my $bleat (@bleat_id) {
        open F, $bleat or die;
        my $bleat_text = "";
        for (sort <F>) {
            if (/^bleat/) {
                $bleat_text .= $_;
            }
        }
        
        if ($bleat_text =~ /$search_term/) {
            $bleat_index++;
            if ($bleat_index <= ($PAGE_INDEX * $NUM_RESULTS)) {
                next;
            } elsif ($bleat_index > (($PAGE_INDEX+1) * $NUM_RESULTS)) {
                next;
            }
            
            print "<div class='bleat' style=\"background-color:#F0F8FF\">";
            seek F, 0, 0;
            
            for (sort <F>) {
                print "<p>$_</p>";
            }
            print "</div>";
            if ($cookies{'auth'} eq "Freelancer") {        
                print <<eof;
<form method="POST">
    <input type="hidden" name="approve" value=$id>
    <input type="submit" name="Approve">
</form>
<form method="POST">
    <input type="hidden" name="disapprove" value=$id>
    <input type="submit" name="Disapprove">
</form>
eof
            }

            close F;
        }
    
    } 
    print "<p></p>";
    print "<a href=?Search=$search_term&page_index=".($PAGE_INDEX-1).">Prev page</a>" if ($PAGE_INDEX);
    print "<a href=?Search=$search_term&page_index=".($PAGE_INDEX+1).">Next page</a>" if ($bleat_index > ($PAGE_INDEX+1) * $NUM_RESULTS);
}

sub search_results {
	my $name = param('search_term'); #the search term
	my $n = 0;
        my $user_index = 0;
        my $match = 0;
        print "<div> <h2> Search Results for ".param('search_term')." </h2>";
	for my $user_folder (sort(glob("$users_dir/*"))) { #for each user
            $match = 0;
            open $user, $user_folder."/details.txt"; #open their details file
            (my $username = $user_folder) =~ s/$users_dir\///; #remove the directory name

	    if ($username =~ /$name/i) { #matches the username
                $match = 1;
			
            } else { #check if matches the users full name
                for (<$user>) {
                    if (/full_name:.*$name/i) {
                        $match = 1;			
                        last;
                    }
                }
            }
        if ($match) {
            $user_index++;
            if ($user_index <= ($PAGE_INDEX * $NUM_RESULTS)) {
                next;
            } elsif ($user_index > (($PAGE_INDEX+1) * $NUM_RESULTS)) {
                next;
            } else {
                print_link_to_user($n, $username);
            }
            
        }
		$n++;
	}
    print "<p></p>";
    print "<a href=?search_term=$name&page_index=".($PAGE_INDEX-1).">Prev page</a>" if ($PAGE_INDEX);
    print "<a href=?search_term=$name&page_index=".($PAGE_INDEX+1).">Next page</a>" if ($user_index > ($PAGE_INDEX+1) * $NUM_RESULTS);	
    print "</div>";
}

sub print_link_to_user {
	my $n = $_[0];
	my $username = $_[1];
    print <<END_OF_HTML;
    <a href="?n=$n"> $username </a><p></p>
END_OF_HTML
    return;
	print <<END_OF_HTML;
<form method="POST" action="">
    <input type="hidden" name="n" value="$n">
    <input type="submit" value="$username" class="btn">
</form>
END_OF_HTML
}


sub print_search_bar {
    print <<eof;
<div id = search_bar>
	<form class="form-inline" method="POST" action="">
		<label>Search Users :</label>
		<input type="text" name="search_term">
		<input type="submit" value="Search" class="btn">
	     
        <label>Search Bleats:</label>
		<input type="text" name="search_bleat">
		<input type="submit" value="Search" class="btn">
	</form>
   
    
</div>	
eof
}

sub profile(){
    my $toshow = $information{'username'};
    my $user_to_show  = "./$users_dir/$toshow";
     
    my $details_filename = "$user_to_show/details.txt";
    print "<div class=\"bitter_picture\">";
    print "<img src=\"$user_to_show/profile.jpg\" alt=\"User has not uploaded a picture\" >";
    print "</div>";

    open my $p, "$details_filename" or die "can not open $details_filename: $!";
    while (my $line = <$p>){
    chomp $line;
    push @userdetail, "$line\n";
    }
    close $p;
    @userdetail = grep(!/^password: /,@userdetail);
    @userdetail = grep(!/^email: /,@userdetail);
    $details = join '', @userdetail;

    return <<eof
<div class="bitter_user_details">
$details
</div>
<p>
eof

}

#
# Show unformatted details for user "n".
# Increment parameter n and store it as a hidden variable
#
sub show_comp() {
    ##### =>  Complaint list to show is:
    ##### ./$users_dir/$related/list.txt
    #print toggle();
    my $toShow = $information{'username'};
    my $bleats_filename = "./$users_dir/$toShow/list.txt";
    #add complaints to array list
    open my $p, "<", "$bleats_filename" or die "can not open $bleats_filename: $!";
        while (my $line = <$p>){
            chomp $line;
            push @bleatstoprint, "$line";
        }
    close $p;

    #if empty array, print Nothing to show
    if(@bleatstoprint){}
    else{
        print "Nothing to show\n";
        return;    
    }
    #reverse chronological order
    @bleatstoprint = reverse sort @bleatstoprint;
    my $i = 0;
    foreach $element (@bleatstoprint){
        if($i >= 20){ #shows up to first 20 bleats
            last;
        }
        @onebleat = (); #reset onebleat holder
        
        #open bleat, parse information and push into onebleat array
        open my $b, "$bleats_dir/${element}" or die "cannot open $bleats_dir/${element}: $!";;
            push @onebleat, "<div class=\"bitter_user_bleats\"\n>";
            while (my $bleatdetail = <$b>){
                chomp $bleatdetail;
                if($bleatdetail =~ /^time: (.*)/){
                    $epoch = $1;
                    $dt = scalar localtime($epoch);
                    push @onebleat, "$dt\n";
                } elsif ($bleatdetail =~ /(^longitude: )|(^latitude: )/){
                    #ignore
                } elsif ($bleatdetail =~ /^bleat: (.*)/){
                    my $text = $1;
                    push @onebleat,"<b>$text</b>\n";
                } elsif ($bleatdetail =~ /^username: (.*)/){
                    $bleater = $1;
                } else {
                    push @onebleat, "$bleatdetail\n";
                }
            
            }
        close $b;
        
        #turn @onebleat into a single string and push to total array bleats
        $bleat_to_show = join '',@onebleat;
        push @bleats, "$bleat_to_show";
        $i++;
    }

    #print bleats
    foreach $post (@bleats){
       print "$post";
    }
   return;
}




sub print_bleats($) {
    $user_to_show = $_[0];
    
    open my $user, "$user_to_show/details.txt";

    $user_to_show =~ s/.*\///;
    my $bleat_index = 0;
    
    for my $bleat (reverse sort (glob("$bleats_dir/*"))) {
        @bleat = ();

        open my $b, "$bleat" or die;
        
        $bleat_index++;
        if ($bleat_index <= ($PAGE_INDEX * $NUM_RESULTS)) {
            next;
        } elsif ($bleat_index > (($PAGE_INDEX+1) * $NUM_RESULTS)) {
            next;
        }

	print "<div class='bleat' style=background-color:#F0F8FF;>";
        seek $b, 0, 0;
        for (my $line = <$b>) {
            push @bleat, "$_ \n";
        }
        print "<div class=\"well\">";
        $bleatresult = join '', @bleat;
        print $bleatresult,"<p><br><p></div>";

        (my $bleat_reply_id = $bleat) =~ s/.*\///; #gets the bleat_id
        
        print "<a href=?bleat_reply=$bleat_reply_id>Reply</a>"  if ($logged_in);
		print "</div>";
    }
    print "<a href=?&page_index=".($PAGE_INDEX-1).">Prev page</a>" if ($PAGE_INDEX);
    print "<a href=?page_index=".($PAGE_INDEX+1).">Next page</a>" if ($bleat_index > ($PAGE_INDEX+1) * $NUM_RESULTS);
}


#
# HTML placed at the top of every page
#
sub page_header {
    #apply my styles first before bootstrap
    return <<eof
Content-Type: text/html

<!DOCTYPE html>
<html lang="en">
<head>
<title>Bitter</title>
<link href="bitter.css" rel="stylesheet">
<link rel="stylesheet" href="https://maxcdn.bootstrapcdn.com/bootstrap/3.3.5/css/bootstrap.min.css">
<style>
  btn btn-default {
    padding-top: 60px;
  }
</style>

</head>
<body>
<nav class="navbar navbar-default">
  <div class="container-fluid">
    <!-- Brand and toggle get grouped for better mobile display -->
    <div class="navbar-header">
      <button type="button" class="navbar-toggle collapsed" data-toggle="collapse" data-target="#bs-example-navbar-collapse-1" aria-expanded="false">
        <span class="sr-only">Toggle navigation</span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
        <span class="icon-bar"></span>
      </button>
      <a class="navbar-brand" href="http://cgi.cse.unsw.edu.au/~z5019263/cgi-hackathon/bitter.cgi">Korrum</a>
    </div>

    <!-- Collect the nav links, forms, and other content for toggling -->
    <div class="collapse navbar-collapse" id="bs-example-navbar-collapse-1">
      <ul class="nav navbar-nav">
         <li><form method="POST" action="">
        <input type="hidden" name="formpage" value="1">
        <input type="submit" value="Post" class="btn">
        </form></li>
        <li><form method="POST" action="">
        <input type="hidden" name="log" value="1">
        <input type="submit" value="History" class="btn">
        </form></li>
        <li><form method="POST" action="">
        <input type="hidden" name="settings" value="1">
        <input type="submit" value="Account" class="btn">
        </form></li>
      </ul>
      <form class="navbar-form navbar-left" role="search">
        <div class="form-group">
          <input type="text" class="form-control" placeholder="Search" name="Search">
        </div>
        <button type="submit" class="btn btn-default">Search</button>
      </form>
    </div><!-- /.navbar-collapse -->
  </div><!-- /.container-fluid -->
</nav>

<div class="container">
eof
}
sub print_logout {
    print <<END_OF_HTML;
<p></p><p></p><p></p><p></p>    
<div class='nav' >
    <form method="POST" action="">
        <input type="hidden" name="logout" value="1">
        <input type="submit" value="Logout" class="btn">
    </form>
</div>
END_OF_HTML
    $logged_in = 1;
}
#
# HTML placed at the bottom of every page
# It includes all supplied parameter values as a HTML comment
# if global variable $debug is set
#
sub page_trailer {
    print "</div>\n";
    my $html = "";
    $html .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
    $html .= end_html;
    return $html;
}

sub send_notification_email() {
        my @list=();
        my $related = $info{"tag"};

        #retrieve email or organisation
        open F, "./$users_dir/$related/details.txt" or die "cannot open ./$users_dir/$related/details.txt: $!";
        while(my $line = <F>){
            chomp $line;
            if($line =~ /^email: (.*)/){
                my $groupemail = $1;
            }
        }
        close F;
        push @list, $info{'id'}."\n";

        #read/copy list of complaint IDs
        open FILE, "./$users_dir/$related/list.txt" or die "cannot open ./$users_dir/$related/list.txt: $!";
        while(my $line = <FILE>){
            push @list, $line;
        }
        close FILE;

        #add new complaint id and overwrite list.txt
        open G, '>',"./$users_dir/$related/list.txt" or die "cannot open ./$users_dir/$related/list.txt";
        foreach $element (@list){
            print G "$element";
        }
        close G;

        #random link currently. change later. should redirect to a page that shows one complaint
        my $link = "http://cgi.cse.unsw.edu.au/~z5019263/cgi-hackathon/bitter.cgi?viewId=".$info{'id'};
        #my $email = "nevin.lazarus\@gmail.com";
        my $from = "z5019263\@cse.unsw.edu.au";
        my $subject = "Complaint";
        my $message = "You've received a complaint! Click here to see it: $link\n ";
        open(MAIL, "|/usr/sbin/sendmail -t");
        # Email Header
        print MAIL "To: $groupemail\n";
        print MAIL "From: $from\n";
        print MAIL "Subject: $subject\n\n";
        # Email Body
        print MAIL $message;
        close(MAIL);  
          
}

#prints out a feed of complaints
sub print_feed() {
    search_feed(".");
}

#Search for complaints
#First argument is the search term
sub search_feed($) {
    $id = 0;
    my $search_term = CGI::escapeHTML($_[0]);     
    for $complaint_file (sort(glob("$bleats_dir/*"))) {
        #check if the file contains the search term
        open(F, $complaint_file) or break; 
        $print_complaint = 0;
        for $line (<F>) {
            if ($line =~ /^(KTP|name)/) {
                next;
            }
            if ($line =~ /$search_term/) {
                $print_complaint = 1;
            } 
        }
        if ($print_complaint) { #if the file contains the search term
    
            open(F, $complaint_file) or break;  
                @bleat = ();           
                for $line (<F>) {
                    if ($line =~ /^(KTP|name)/) {
                        if ($line =~ /name: (.*)/) {
                            $id = $1;
                        }
                        next;
                }

                push @bleat, "<p>$line </p>\n";
            }

                print "<div class=\"well well-sm\">";
                $bleatresult = join '', @bleat;
                print $bleatresult,"</div>";




        }
    } 
}
    



sub post(){
    #my $KTP = $information["KTP"];
    #my $name = $information["name"];
    my $id = localtime;
    $id =~ s/[^\d]//g;
    return <<eof;
    <div class="jumbotron">
    <h1>Let's fight corruption together.</h1>
    <form method="POST">
    <input class="btn" style="display:inline-block" type="file" name="upload"> <p>
    Description: <p><textarea default="Describe the incident" class="form-control" rows="5" name="description"> </textarea>
    <p>
    Location/Organisation: <input type="text" name="location"> <p>
    <input type="hidden" name="id" value=$id>
    <input type="hidden" name="post_write" value="True">
    <input type="submit" name="submit">
</form>
</div>
eof
}

sub post_write {
    %info = ();
    $info{"KTP"} = $information{"idnum"};
    $info{"name"} = $information{"username"};
    $info{"id"} = param("id");
    $info{"location"} = param("location");
    $info{"description"} = param("description");
    $info{"rep"} = $information{"rep"};
    my $file = "/bleats/".$info{"id"}.".txt";

    open (FILE, '>',".$file") or die "\nunable to create .$file\n";
    
    foreach $i (sort(keys %info)){
        if ($i ne "id"){
            $tmp = $info{$i};
            print FILE "$i: ".($tmp)."\n";

	    }
    }
    close FILE;

    if($info{"tag"}){
        send_notification_email();
    }

}


main();

