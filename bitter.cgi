#!/usr/bin/perl -w

# written by andrewt@cse.unsw.edu.au September 2015
# as a starting point for COMP2041/9041 assignment 2
# http://cgi.cse.unsw.edu.au/~cs2041/assignments/bitter/

use CGI qw/:all/;
use CGI::Cookie;
use CGI::Carp qw/fatalsToBrowser warningsToBrowser/;
use Mail::Sendmail;

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

	%name_to_int;
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
        if (defined $cookies{'auth'} && $cookies{'auth'}->value ne 0) { #logged in already
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
    
	
    if (param('confirm_user')) {
    	create_user_account();
    }
    
    if (param('sign_user') && (param('sign_pass') eq param('confirm_pass')) && param('sign_email') =~ /\@/) {
	send_account_confirm();
    } elsif (param('signup')) {
	sign_up_screen();
        org_sign_up();
    }
    
    print page_trailer();
}


#---------------------------------------------------#
# ACCOUNT RELATED FUNCTIONS                                       #
#---------------------------------------------------#

sub print_login {
    #<input type="submit" value="Forgot Password" class="btn"> TODO add later
    print <<END_OF_HTML;
<div class='nav'>
    <form method="POST" action="">
        <label>Username:</label>
        <input type="text" name="username">
        <label>Password:</label>
        <input type="password" name="password">
        <input type="submit" value="Login" class="btn">
    </form>
    <form method="POST" action="">
        <input type="hidden" name="signup" value=1>
        <input type="submit" value="Sign-up" class="btn">
    </form>
</div>
END_OF_HTML
    $logged_in = 0;
}

sub print_logout {
    print <<END_OF_HTML;
<div class='nav' >
    <form method="POST" action="">
        <input type="hidden" name="logout" value="1">
        <input type="submit" value="Logout" class="btn">
    </form>
</div>
END_OF_HTML
    $logged_in = 1;
}
#complete!
sub create_user_account {
	my $new_user = param('confirm_user');
	my $new_pass = param('password');
	my $new_email = param('email');
	my $uniqId = param('uniqId');
        my $org = param('group');
        mkdir("./$users_dir/temp/$new_user");
	open DETAILS, ">$users_dir/temp/$new_user/details.txt";
	print DETAILS "username: $new_user\n";
	print DETAILS "password: $new_pass\n";
	print DETAILS "email: $new_email\n";
	print DETAILS "idnum: $uniqId\n";
        print DETAILS "org: $org\n";
	close DETAILS;
}

sub send_account_confirm {
	my $email = param('sign_email');
	my $username = param('sign_user');

        #check if username exists
	if (-d "$users_dir/$username" || -d "$users_dir/temp/$username") {
		print "Username is already taken";
		return;
	}
	
	my $password = param('sign_pass');
	my $from = "z5019263\@cse.unsw.edu.au";
	my $subject = "Confirm";
	my $message = "cse.unsw.edu.au/~z5019263/ass2/bitter.cgi?confirm_user=$username";
	print "Sending mail to $email", ;
	open(MAIL, "|/usr/sbin/sendmail -t");
	# Email Header
	print MAIL "To: $email\n";
	print MAIL "From: $from\n";
	print MAIL "Subject: $subject\n\n";
	# Email Body
	print MAIL $message;

	close(MAIL);
	
}

sub org_sign_up{
    print "<br><br><h3>Create a new account</h3><p>";
    print "Only alphanumeric  characters, underscores and dashes are allowed<p> for username and password, to a maximum of 30 characters.<p>";
    print start_form, "\n";
    
    print "Username:\n", textfield( -name=>'newusr',
                                            -override=>1, 
                                            -pattern=>"[A-Za-z0-9_\-]+",
                                            -maxlength=>30), "\n<br>";
    print "Password:\n", password_field(-name=>'newpwd',
                                                    -override=>1,
                                                    -pattern=>"[A-Za-z0-9_\-]+",
                                                    -maxlength=>30), "<br>\n";
    print "Identification No:\n", password_field(-name=>'newpwd',
                                                                -override=>1,
                                                                -pattern=>"[0-9]+",
                                                                -maxlength=>20), "<br>\n";
    print "Email:\n", textfield(-name=>'email',
                                        -pattern=>"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+[a-zA-Z0-9]",
                                        -override=>1), "<br>\n";
    print hidden('group',"true");
    print submit('newaccount','Create'), "\n";
    print end_form, "\n"; 
}
sub sign_up_screen {
	print <<eof;
	
	<h2> Sign Up </h2>	
<form method="POST" action="">
    <table cellspacing=10> 
        <tr>    
	        <td> <label class="signup">Username:</label> </td>
	        <td> <input type="text" name="sign_user"> </td>
        </tr>
        <tr>
	        <td> <label class="signup">Indonesian ID:</label> </td>
	        <td> <input type="text" name="sign_uniqId"> </td>
        </tr>
        <tr>
	        <td> <label class="signup">Password:</label> </td>
	        <td> <input type="password" name="sign_pass"> </td>
	    </tr>
	    <tr>
	        <td> <label class="signup">Confirm Password:</label> </td>
	        <td> <input type="password" name="confirm_pass"> </td>
	    </tr>
	    <tr>
	        <td> <label class="signup">Email:</label> </td>
	        <td> <input type="text" name="sign_email"> </td>
	    </tr>
	    <tr>
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
    print BLEAT_LIST (int($bleat_id[0])+1), "\n";
    
    close BLEAT_LIST;
}

#---------------------------------------------------#
# GENERAL FUNCTIONS                                                  #
#---------------------------------------------------#
sub list_users(){
    my @users = <./$users_dir/*>;
    my $directory = quotemeta"$users_dir";
    @users = grep(!/temporary/,@users);
    foreach my $user (@users) {
               $user =~ s/\.\/$directory\///;
               print '<form method="POST" action="">';
               print "<input type=\"hidden\" name=\"username\" value=\"$username\">";
               print  "<input type=\"hidden\" name=\"loggedin\" value=\"$loggedIn\">";
               print "<input type=\"submit\" name=\"userprofile\" value=\"$user\" class=\"user_button\">\n";
               print "</form>";
    
    }
    return;
}
sub buffer_details(){
    my $user_to_show  = "./$users_dir/$username";
    my $details_filename = "$user_to_show/details.txt";
    open my $p, "$details_filename" or die "can not open $details_filename: $!";
    while (my $line = <$p>){
        chomp $line;
        if ($line =~ /^listens: (.*)/){
            @listens = split(' ',$1);
            #$information{"listens"}= \@listens;
        }elsif($line =~ /([^:]+): (.*)/){
            $information{"$1"}= "$2";
        }
    }
    close $p;
}



sub message_box {
    my $bleat_reply = param('bleat_reply') || ""; 
    print <<END_OF_HTML;
<div>
    <form method="POST" action="">
        <input type="text" name="message" maxlength="142">
        <input type="hidden" name="bleat_reply" value="$bleat_reply">
        <input type="submit" value="Send Message" class="btn">
    </form>
</div>
END_OF_HTML
}

#---------------------------------------------------#
# SEARCH FUNCTIONS                                                  #
#---------------------------------------------------#

sub search_bleats {
    my $search_term = param('search_bleat');
    my @bleat_id = reverse (sort(glob("$bleats_dir/*")));
    
    print "<h2> Bleat Results for ".param('search_bleat')." </h2>";
    my $bleat_index = 0;
    for my $bleat (@bleat_id) {
        open F, $bleat or die;
        my $bleat_text = "";
        for (sort <F>) {
            if (/^bleat/) {
                $bleat_text = $_;
            }
        }
        $bleat_text =~ s/^bleat: //;        
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
                print $_."<br>";
                
            }
            (my $bleat_reply_id = $bleat) =~ s/.*\///; #gets the bleat_id
            print "<a href=?bleat_reply=$bleat_reply_id>Reply</a>" if ($logged_in);
            print "<br>";
            print "</div>";
        }
        close F;
    }
    print "<br>";
    print "<a href=?search_bleat=$search_term&page_index=".($PAGE_INDEX-1).">Prev page</a>" if ($PAGE_INDEX);
    print "<a href=?search_bleat=$search_term&page_index=".($PAGE_INDEX+1).">Next page</a>" if ($bleat_index > ($PAGE_INDEX+1) * $NUM_RESULTS);
}

sub search(){
    $query = param('query');
    print "<div class=\"search\">";
    print start_form, "\n";
    print "Search \n", textfield('query'), "\n";
    print hidden('username',"$username"),"\n";
    print hidden('loggedin',"$loggedIn"),"\n";
    print submit('search','Search'), "\n";
    print end_form, "\n";
    print "</div>\n";
    $keyword = quotemeta "$query";
    $directory = quotemeta"$users_dir";
    $bleatdir = quotemeta"$bleats_dir";
    if (defined $keyword && $keyword ne ''){

        
        #check users
        print "<h4>Related Users</h4>";
        
        
        #match by username
        my @users = <./$users_dir/*>;
        %userresults = ();
        foreach $user (@users){
            open   (F, "$user/details.txt");
            while (my $detail = <F>){
                if ($detail =~ /^full_name: (.*)/){
                    my $fullname = $1;
                    if (($fullname =~ /$keyword/i || $user =~ /$keyword/i)){
                        $user =~ s/\.\/$directory\///;
                        $userresults{"$user"} = $fullname;
                    }      
                }
               
            }
            close F;
        
        }
       
        print "<div class=\"results\"\n>";

       if (%userresults){
            
            foreach my $key (keys %userresults) {
               print '<form method="POST" action="">';
               print "<input type=\"hidden\" name=\"username\" value=\"$username\">";
               print  "<input type=\"hidden\" name=\"loggedin\" value=\"$loggedIn\">";
               print "<input type=\"submit\" name=\"userprofile\" value=\"$key\" class=\"profile_button\">\n";
               print "</form>";
               print "Full name: $userresults{$key}\n";
                
            }
        } else {
            print "nothing found!\n";
        }
        print "</div><p><br>";
        
        #check bleats
        print "<h4>Related Bleats</h4>";
        my @files = <./$bleats_dir/*>;
        $yes = 0;
        foreach my $file (@files) {

            @onebleat = ();
            open   (FILE, "$file");
            push @onebleat, "<div class=\"bitter_user_bleats\"\n>";
            while(my $line= <FILE> ){
                chomp $line;
                if ($line =~ /^bleat: (.*)/){
                    $tocheck = $1;
                    if ($tocheck =~ /$keyword/i){
                        $yes = 1;
                    } else {
                        $yes = 0;
                    }   
                    push @onebleat, "<b>$tocheck</b>\n";
                } elsif($line =~ /^time: (.*)/){
                    $difference = $1;
                    $dt = DateTime->new( year       => 1970,
                                          month      => 1,
                                          day        => 1,
                                          time_zone  => "Australia/Sydney",
                                         );
                    $dt->add(seconds => $difference);
                    $dt =~ s/T/ /;
                    push @onebleat, "$dt\n";
                } elsif ($line =~ /^username: (.*)/){
                    
                    $bleater = $1;

  
                } elsif ($line =~ /(^longitude: )|(^latitude: )/){
                    #ignore
                } else {
                    push @onebleat, "$line\n";
                }
            }
            close FILE;
            push @onebleat, '<form method="POST" action="">';
            push @onebleat, "<input type=\"hidden\" name=\"username\" value=\"$username\">";
            push @onebleat, "<input type=\"hidden\" name=\"loggedin\" value=\"$loggedIn\">";
            push @onebleat, "<input type=\"submit\" name=\"userprofile\" value=\"$bleater\" class=\"profile_button\">";
            push @onebleat, "</form>";
            $element = $file;
            $element =~ s/\.\/$bleatdir\///;
            push @onebleat, '<form method="POST" action="">';
            push @onebleat, "<input type=\"hidden\" name=\"username\" value=\"$username\">";
            push @onebleat, "<input type=\"hidden\" name=\"loggedin\" value=\"$loggedIn\">";
            push @onebleat, "<input type=\"hidden\" name=\"bleattoshow\" value=\"$element\" >";
            push @onebleat, "<input type=\"submit\" name=\"userprofile\" value=\"reply\" class=\"profile_button\">";
            push @onebleat, "</form>";

            push @onebleat, "</div>\n";
            if ($yes == 1){
                $bleatresult = join '', @onebleat;
                push @bleats, $bleatresult;
            } 
            
        }
        foreach $thingy (@bleats){
            print "$thingy";
        }
    }
    return;
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
    print "<br>";
    print "<a href=?search_term=$name&page_index=".($PAGE_INDEX-1).">Prev page</a>" if ($PAGE_INDEX);
    print "<a href=?search_term=$name&page_index=".($PAGE_INDEX+1).">Next page</a>" if ($user_index > ($PAGE_INDEX+1) * $NUM_RESULTS);	
    print "</div>";
}

sub print_link_to_user {
	my $n = $_[0];
	my $username = $_[1];
    print <<END_OF_HTML;
    <a href="?n=$n"> $username </a><br>
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

#
# Show unformatted details for user "n".
# Increment parameter n and store it as a hidden variable
#
sub user_page {
    my $n = param('n') || 0;
    @users = sort(glob("$users_dir/*"));
	
    my $user_to_show  = $users[$n % @users];
    my $details_filename = "$user_to_show/details.txt";
    my $image_filename = "$user_to_show/profile.jpg";
    open F, "$details_filename" or die "can not open $details_filename: $!";
	my $details;
    for (sort <F>) { 
        if (!defined $_) {
            next;
        }
        s/^/<li>/;
        if (/listen/) { #changes to a list format
            s/listens:/listens:<ul>/; 
            s/ ([A-Z][A-Za-z0-9]+)/<li> $1 <\/li>/g;
            s/$/<\/ul>/;            
        } else {            
            s/.*(username|password|email): [^ <]+//g; #remove the password and email fields;        
        }
        $details .= $_;       
    }
    my $listen_buttons;
    if ($logged_in) {
    
        print <<eof;
<div>
    <form  method="post" action="" enctype="multipart/form-data">
        <input style="display:inline-block" type="file" name="upload">
        <input style="display:inline-block" type="submit" name="upload" value="Upload profile pic">
    </form>
</div>
eof
    
        my $listening = "Listen";
		fetch CGI::Cookie;
        open my $user_auth, "$users_dir/".$cookies{'auth'}->value."/details.txt";
        for (<$user_auth>) {
            if (/listen/) {
                (my $other_name = $user_to_show) =~ s/.*\///;
                if (/$other_name/) { #already listening
                    $listening = "Unlisten";
                }
            }
        }
        
        $listen_buttons = <<eof;
<form style="display:inline-block" method="POST" action="">
    <input type="hidden" name="listen" value="$n">
    <input type="submit" value="$listening" class="btn">
</form>
    
eof
    } else {
        $listen_buttons = ""; #cannot listen to user if not logged in
    }
    close F;
    my $next_user = $n + 1;
	my $prev_user = $n - 1;
    (my $username = $user_to_show) =~ s/.*\///;
    print <<eof;	

<div>
    <form style="display:inline" method="POST" action="">
        <input type="hidden" name="n" value="$prev_user">
        <input type="submit" value="Previous user" class="btn">
    </form>

    <form style="display:inline" method="POST" action="">
        <input type="hidden" name="n" value="$next_user">
        <input type="submit" value="Next user" class="btn">
    </form>
</div>

<table>
<tr>
<td valign=top>
    <div class="bitter_user_details" align=top style="display:inline-block">
        
        <img width="300px" height="300px" src=$image_filename onerror="this.src='nopicture.jpg'" align="middle" />
        <form style="white-space: pre-line;word-wrap:break-word;display:inline-block">
            <h2> $username </h2>
            $details
        </form>
        $listen_buttons
    </div>
</td>
<td>
    <div>
eof
	print_bleats($user_to_show);
    print "</div></td><tr></table>";
}



sub print_bleats($) {
	$user_to_show = $_[0];
    
    open my $user, "$user_to_show/details.txt";
    my $listeners = "";
    for (<$user>) {
        if (/^listens/) {
            $listeners = $_; #find the line with listeners
            last;
        }
    }
    $user_to_show =~ s/.*\///;
    
    my $bleat_index = 0;
    
    for my $bleat (reverse sort (glob("$bleats_dir/*"))) {
        
        open my $b, "$bleat" or die;
        
        my $include = 0;
        for (<$b>) {
            if ($logged_in && $cookies{'auth'}->value eq $user_to_show) { #can view bleats related to the logged in use
                if (/$user_to_show/) {
                    $include = 1;
                    last;
                } elsif (/username: /) {
                    s/username: //; #removes the field name
                    if ($listeners =~ /$_/) { #the user is being listened to
                        $include = 1;
                        last;
                    }
                }
            } else {
                if (/username: $user_to_show/) {
                    $include = 1;
                    last;
                }
            }
        }
        if (!$include) {
            next;
        }
        $bleat_index++;
        if ($bleat_index <= ($PAGE_INDEX * $NUM_RESULTS)) {
            next;
        } elsif ($bleat_index > (($PAGE_INDEX+1) * $NUM_RESULTS)) {
            next;
        }

		print "<div class='bleat' style=background-color:#F0F8FF;>";
        seek $b, 0, 0;
        for (sort <$b>) {

            print $_."<br>";
        }
        (my $bleat_reply_id = $bleat) =~ s/.*\///; #gets the bleat_id
        
        print "<a href=?bleat_reply=$bleat_reply_id>Reply</a>"  if ($logged_in);
		print "</div>";
    }
    
    print "<br>";
    print "<a href=?n=".param('n')."&page_index=".($PAGE_INDEX-1).">Prev page</a>" if ($PAGE_INDEX);
    print "<a href=?n=".param('n')."&page_index=".($PAGE_INDEX+1).">Next page</a>" if ($bleat_index > ($PAGE_INDEX+1) * $NUM_RESULTS);
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


</head>
<body>
eof
}


#
# HTML placed at the bottom of every page
# It includes all supplied parameter values as a HTML comment
# if global variable $debug is set
#
sub page_trailer {
    my $html = "";
    $html .= join("", map("<!-- $_=".param($_)." -->\n", param())) if $debug;
    $html .= end_html;
    return $html;
}

sub send_notification_email() {
    my $email = "nevin.lazarus\@gmail.com";
	my $from = "z5019263\@cse.unsw.edu.au";
	my $subject = "Complaint";
	my $message = "You've received a complaint!";
	open(MAIL, "|/usr/sbin/sendmail -t");
	# Email Header
	print MAIL "To: $email\n";
	print MAIL "From: $from\n";
	print MAIL "Subject: $subject\n\n";
	# Email Body
	print MAIL $message;
	close(MAIL);    
}


sub Ret {
    my $KTP = $information["KTP"];
    my $name = $information["name"];
    return <<eof
<form method="POST">
    <input style="display:inline-block" type="file" name="upload">
    <input style="display:inline-block" type="submit" name="upload" value="Upload profile pic">

    <input type="text" name="description">
    <input type="hidden" name="KTP" value=$KTP>
    <input type="hidden" name="name" value=$name>
    




    <input type="submit" name="submit">


</form>

eof
}


main();

