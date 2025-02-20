#!/gov/ecf/bin/perl


#dkw This file is a copy of fees1-rpt.pl to fees_odst.pl to make this specific to LAWB Order of Distribution 09/12/2007
use lib '../support';
require '../site/SiteSetup.pl';
require '../support/setup.pl';
require '../support/Site.pm';
require '../support/routines.pl';
require '../support/html-lib.pl';
require '../support/SysRoutines.pl';
require '../support/autoloadhelper.pm';

%Var;
tie %Var,'Site';
select(STDOUT); $| = 1; # make it flush
$Id = $ContextFileId = GetPrefixFileName();
LockFile("/tmp/$Id");
$Var{"version"} = 'ident "rcsid=$Header: /usr/local/cvsroot/util/bin/hsgs,v 4.3 2006/02/13 21:40:40 sirotta Exp $"';
Globals();
# Trap exit signals
$SIG{'INT'} = 'ExitHandler';
$SIG{'TERM'} = 'ExitHandler';
$SIG{'QUIT'} = 'ExitHandler';
$SIG{'TERM'} = 'ExitHandler';
$SIG{'PIPE'} = 'ExitHandler';
if($ConType eq "local") {
        my $Directive = "set lock mode to wait 20; set isolation to dirty read;";

        if ($SqlOut eq "ON" ) {
                $Directive = "set lock mode to wait 20; set isolation to dirty read;set explain on";
        }
                # if enabled wait for lock...then lock...then go onward
                flockOn("/tmp/sqexplain.out") if $SqlOut eq "ON";  #So../tmp/sqexplain.out.LOCK
                if(SQL::bConnectDb($DBNAME) == 0) {
                        DisplayDBConnectFailureMsg();
                        print STDERR "ERROR:Could not connect to database ($DBNAME).
";
            flockOff("/tmp/sqexplain.out") if $SqlOut eq "ON";
                        exit(0);
                }
                if(BeginWork() == 0) {
                        DisplayDBConnectFailureMsg();
                        print STDERR "ERROR:Could not issue a Begin Work directive to ($DBNAME). Please check the logging mode of the database.
";
            flockOff("/tmp/sqexplain.out") if $SqlOut eq "ON";
                        exit(0);
                }
                if( SQL::bDoSql($Directive) == 0) {
                        DisplayDBConnectFailureMsg();
                        print STDERR "ERROR:Could not issue the following directive ($Directive) to database  ($DBNAME).
";
            flockOff("/tmp/sqexplain.out") if $SqlOut eq "ON";
                        ExitCleanup();EcfExit(0);
                }

    }
        # CHECK if this is a re-entry, if so goto place specified in QUERY_STRING

#dkw Modified fees1-rpt.pl to fees_odst.pl to make this specific to LAWB Order of Distribution 09/12/2007
$MyName = "fees_odst.pl";
$main::EnableRedirect = 0;
$main::EnablePacerBilling = 0;
$Param = $ENV{"QUERY_STRING"};
        $From = $ENV{"HTTP_REFERER"};
        my $HistLabel = $3;
        $Var{FromURL} = $From;
                $Var{NextURL} = "$ENV{SCRIPT_NAME}?$Id-UNKNOWN-0".$NextURL;
        if ($Param =~ /([a]?[0-9]+)-(L_[0-9]+_[0-9]+)-([0-9])-([\w]+)/ ||
                $Param =~ /([a]?[0-9]+)-(L_[0-9]+_[0-9]+)-([0-9])/ ||
                $Param =~ /([a]?[0-9]+)-([\w]+)/ ||
                $Param =~ /([a]?[0-9]+)/
) {
                my $VarFile = "/tmp/".$1;
                my $P2 = $2;
                my $P3 = $3;
                my $P4 = $4;
                if($P2 =~ /L_/) {
                        $Goto = $P2;
                } elsif($P4) {
                        $OptParam = $P4;
                }else {
                        $Goto = "";
                        $OptParam = $P2;
                }
                $IsForm = $P3;
                my $FromURL = $Var{FromURL};
                $From =~ /([^\?]+)\?*./;
                my $FromURL = $Var{FromURL};
                $NextURL = $Var{NextURL};
                if ($IsForm eq "1" and ($ENV{CONTENT_TYPE} =~ /form-data/i or $ENV{CONTENT_TYPE} =~ /application\/x-www-form-urlencoded/i) ) {
                        UnCgi();        # FIRST GET ANY FORM DATA (PLACE IN Var{}).
                }
                if($VarFile && (-r $VarFile)) {
                        WaitForLock($VarFile);
                        LoadContextFile($VarFile);
                }
                $Var{EnableDBAccess} = 1;
                $Var{NextURL} = $NextURL;
                $Var{FromURL} =  $FromURL;
                TodaysDate();
                if ($Goto) {
                        my $Key;
                        foreach $Key (keys %VarTmp) {
                                if(! ($Key =~ /:/)) {
                                $Var{$Key} = $VarTmp{$Key};
                                } else {
                                        my $FieldName = $Key;
                                        my $AssocName = "Var";
                                        my $SpaceName = "main";
                                        if($FieldName =~ /([\w]+)::([\w]+):([\w]+)/) {
                                                $SpaceName = $1;
                                                $AssocName = $2;
                                                $FieldName = $3;
                                        } elsif($FieldName =~ /([\w]+):([\w]+)/) {
                                                $AssocName = $1;
                                                $FieldName = $2;
                                        } elsif($FieldName =~ /([\w]+)::([\w]+)/) {
                                                $SpaceName = $1;
                                                $FieldName = $2;
                                        }
                                        AddAssocNameToList($SpaceName."::".$AssocName);
                                        my $EV = "\$".$SpaceName."::".$AssocName."{".$FieldName."} = '".$VarTmp{$Key}."';";
                                        eval($EV);
                                if($@) {
                                        die("EVAL FAILED in hsgs generated source with $@");
                                        }
                                }
                        }
                        if($DebugFile) {
                                print RUNFILE "`echo \"About to reenter runtime stream at $Goto.\" >> $DebugFile`;";
                        }
                        $Var{CurrentURL} = $Var{NextURL};
                        goto $Goto;
                } else {
                        $Var{CurrentURL} = "$ENV{SCRIPT_NAME}";

                }
        } else {

                TodaysDate();
        }
        $Var{EnableDBAccess} = 1;
# Perl Code for Event fees1-rpt.hsgs
# #ident "rcsid=$Header: /usr/local/cvsroot/bankruptcy/web/hsgs/fees1-rpt.hsgs,v 3.1 2003/04/25 11:56:15 loy Exp $"


#Line 0:
# Global ($EventTitle = "Awarded Professional Fees by Recipient";$EventName = "Awarded Professional Fees by Recipient";);


#Line 1:
# Enable Security;


#Line 2:
# Begin HTML("{SystemName} - {EventTitle}");

PrintContent("{SystemName} - {EventTitle}","onLoad='SetFocus()'");
PrintString("<SCRIPT LANGUAGE=\"JavaScript\">
                var IsForm = false;
                var FirstField;
                function SetFocus() {
                        if(IsForm) {
                                if(FirstField) {
                                        var ind = FirstField.indexOf('document.',0);
                                        if(ind == 0)
                                        {
                                                eval(FirstField);
                                        }
                                        else
                                        {
                                                var Code = \"document.forms[0].\"+FirstField+\".focus();\";
                                                eval(Code);
                                        }
                                } else {
                                        var Cnt = 0;
                                        while(document.forms[0].elements[Cnt] != null) {
                                                if(document.forms[0].elements[Cnt].type != \"hidden\") {
                                                        document.forms[0].elements[Cnt].focus();
                                                        break;
                                                }
                                                Cnt += 1;
                                        }
                                }
                        }
                        return(true);
                }
                </SCRIPT>
");
        $main::SendJobResultBytes=0;

        if (VerifyAccess() == 0) {
                EndHtml();
                ExitCleanup();EcfExit(0);
        }

#Line 3:
# Begin Form;


#dkw Modified fees1-rpt.pl to fees_odst.pl to make this specific to LAWB Order of Distribution 09/12/2007
$Var{NextURL} = "/cgi-bin/fees_odst.pl?$Id-L_866_0-1";
 PrintString(" <FORM ENCTYPE='multipart/form-data' method=POST action=\"/cgi-bin/fees_odst.pl?$Id-L_866_0-1\" >\n");

#Line 4:
# Perl (require '../support/Interface.pl';);

require '../support/Interface.pl';

#Line 5:
# run NewHeader("Professional Fees Awarded");

        my $Ret = NewHeader("Professional Fees Awarded");
                if($Ret == 0) {
                        PrintString("<P><INPUT TYPE=\"button\" Value=\"Back\" onClick=\"history.back()\">");
                        RollbackWork();
                        ExitCleanup();EcfExit(0);
                } elsif ($Ret == 2) {
                if(0 and ($ConType eq "local")) {
                        CommitWork();
                        SQL::bDisConnectDb();
                }
                ExitCleanup();EcfExit(0);
                }

#Line 6:
# Perl (require '../support/ProfessionalFees.pl';);

require '../support/ProfessionalFees.pl';

#Line 7:
# run RecipientFeesScreen();

        my $Ret = RecipientFeesScreen();
                if($Ret == 0) {
                        PrintString("<P><INPUT TYPE=\"button\" Value=\"Back\" onClick=\"history.back()\">");
                        RollbackWork();
                        ExitCleanup();EcfExit(0);
                } elsif ($Ret == 2) {
                if(0 and ($ConType eq "local")) {
                        CommitWork();
                        SQL::bDisConnectDb();
                }
                ExitCleanup();EcfExit(0);
                }

#Line 8:
# End Form ("'Run Report'");


        local(@Valid,$Size,$i);
        @Valid = split(";",$OnSubmit);
        $Size = @Valid;
        PrintString("<SCRIPT LANGUAGE=\"JavaScript\">
                var timerId;
                var BeenHere = 0;
                IsForm  = true;
                function empty(s) {
                        var whitespace = \" \\t\\n\\r\";
                        if(s == null || s.length == 0) {
                                return(true);
                        }
                    // Is s only whitespace characters?
                    for (var i = 0; i < s.length; i++) {
                        var c = s.charAt(i);
                         if (whitespace.indexOf(c) == -1) return false;
                    }
                        return(true);
                }
                function ClearTimer() {
                        BeenHere = 0;
                        clearTimeout(timerId);
                        return(true);
                }
                var FormId = 0;
                function ProcessForm() {
                        if(BeenHere == 1) {
                                alert(\"Submission already made, please wait for response from server\");
                                return(false);
                        }
                        BeenHere = 1;
                        timerId=setTimeout(\"ClearTimer()\",5000);
");
        for ($i = 0; $i < $Size; $i++) {
          PrintString("if( ! $Valid[$i] ) {ClearTimer();return false;}\n");
        }
        foreach $Value (split(";",$FieldList)) {
          PrintString("if( empty($Value.value) ) {$Value.value = \" \"};\n");
        }
PrintString("document.forms[FormId].submit();return true
}");
$RunAfterClear = join ";\n\t", @RunAfterClear;
PrintString("

function RunAfterClear() {
        $RunAfterClear
}");
PrintString("
</SCRIPT>
");
PrintString("<TABLE> <TD><INPUT NAME=\"button1\" Value='Run Report' TYPE=\"button\" ONCLICK=\"ProcessForm()\" >
<TD> <TD><TD> <INPUT NAME=\"reset\" TYPE=\"RESET\" VALUE=\"Clear\" onClick=\"setTimeout('RunAfterClear()',100)\"> <TR></TABLE ></FORM>");
#Line 9:
# End HTML;


                EndHtml();
                WriteVars("/tmp/$Id");
                if(0 and ($ConType eq "local")) {
                        CommitWork();
                        SQL::bDisConnectDb();
                }
                ExitCleanup();EcfExit(0);

L_866_0:

#Line 10:
# Begin HTML("{SystemName} - {EventTitle}");

PrintContent("{SystemName} - {EventTitle}","onLoad='SetFocus()'");
PrintString("<SCRIPT LANGUAGE=\"JavaScript\">
                var IsForm = false;
                var FirstField;
                function SetFocus() {
                        if(IsForm) {
                                if(FirstField) {
                                        var ind = FirstField.indexOf('document.',0);
                                        if(ind == 0)
                                        {
                                                eval(FirstField);
                                        }
                                        else
                                        {
                                                var Code = \"document.forms[0].\"+FirstField+\".focus();\";
                                                eval(Code);
                                        }
                                } else {
                                        var Cnt = 0;
                                        while(document.forms[0].elements[Cnt] != null) {
                                                if(document.forms[0].elements[Cnt].type != \"hidden\") {
                                                        document.forms[0].elements[Cnt].focus();
                                                        break;
                                                }
                                                Cnt += 1;
                                        }
                                }
                        }
                        return(true);
                }
                </SCRIPT>
");
        $main::SendJobResultBytes=0;

        if (VerifyAccess() == 0) {
                EndHtml();
                ExitCleanup();EcfExit(0);
        }

#Line 11:
# Perl (require '../support/ProfessionalFees.pl';);
# dkw Modified require below for report specific to Order of Distribution LAWB 09/12/2007
require '../support/ProfessionalFeesOdst.pl';

#Line 12:
# Last Page;


#Line 13:
# run fees1();

        my $Ret = fees1();
                if($Ret == 0) {
                        PrintString("<P><INPUT TYPE=\"button\" Value=\"Back\" onClick=\"history.back()\">");
                        RollbackWork();
                        ExitCleanup();EcfExit(0);
                } elsif ($Ret == 2) {
                if(0 and ($ConType eq "local")) {
                        CommitWork();
                        SQL::bDisConnectDb();
                }
                ExitCleanup();EcfExit(0);
                }

#Line 14:
# End HTML;


                EndHtml();
                WriteVars("/tmp/$Id");
                if(0 and ($ConType eq "local")) {
                        CommitWork();
                        SQL::bDisConnectDb();
                }
                ExitCleanup();EcfExit(0);

L_866_1:

#Line 15:
#

#Line 16:

exit(0);
#Start of user perl block

#End of User perl block

sub Globals
{
$EventTitle = "Awarded Professional Fees by Recipient";$EventName = "Awarded Professional Fees by Recipient";

}
sub DisplayDBConnectFailureMsg {
        my $Page = "DbConnectFailure.htm";
        if(-f "../html/$Page") {
                PrintContent("Error","");
                ShowPage($Page);
        } else {
                PrintContent("Error","");
                print qq~<html>
<head>
  <meta http-equiv="content-type" content="text/html; charset=ISO-8859-1">
</head>
<body>
An error has occurred while trying to service your request. &nbsp;Please
retry your request in a few minutes.<br>
<br>
</body>
</html>~;
        }
}

sub ExitHandler {
        ExitCleanup();
        EcfExit(0);
}

sub ExitCleanup {
        UnLockFile("/tmp/$Id");
}