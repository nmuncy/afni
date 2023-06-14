#!/usr/bin/env python

# This library contains functions for creating an InstaCorr driver
# script for the AP results directory.
#
auth = 'PA Taylor'
# ver : 0.1 || date: Oct 5, 2022
# + some level of written-ness
#
#ver = 1.1 # date: Oct 16, 2022
# + allow 1D files (e.g., ideal stim files) and plugins in the GUI
#
#ver = 1.2 # date: Nov 15, 2022
# + tweak pop-up msg text and minor function fix
#
#ver = 1.3 # date: June 5, 2023
# + add in ability to take 3 cmd line args to represent initial seed loc
#
ver = 1.4 # date: June 6, 2023
# + create this script to be a general InstaCorr script for all pb*HEAD 
#   files.  It requires cmd line args to run, but it can be used by the
#   APQC HTML relatively conveniently
#
#########################################################################


import os, copy
import sys
import glob
import json
import subprocess

# ----------------------------------------------------------------------

DEF_scriptname = 'run_instacorr_pbrun.tcsh'        # output file, tcsh script

# ===========================================================================
# ===========================================================================
# main text defaults: most of the script is type-cast

text_ic_top     = """#!/bin/tcsh

# This script was created by the afni_proc.py quality control (APQC)
# generator.  
#
# It's purpose is to facilitate investigating the properties of the
# raw/unprocessed input data, using the AFNI GUI's InstaCorr functionality.  
#
# As described in the popup help, users should just need to hold down
# the Ctrl+Shift keys and then left-click and move the mouse around
# (dragging or re-clicking).  Watch the correlation patterns to that
# seed location change, and this often provides an excellent way to
# understand the data.
#
# In this script, one *must* provide 2 command line args: a pb label (pb00, 
# pb01, etc.), and a run number (r01, r02, r03, etc.).
#
# Additionally, one *can* also add three numbers on the command line
# to represent the starting location (RAI coordinate notation) of the 
# initial seed.

# ver = {ver}
# -------------------------------------------------------------------------

""".format(ver=ver)

# ... and functions to define a few quantities are given below:
#     make_apqc_ic_*( ... ) ...

text_ic_bot = """


set pb  = "$1"
set run = "$2"

if ( "${run}" == "" ) then
    echo "** Exiting: this program requires 2 cmd line args to run:"
    echo "   + a pb label (pb00, pb01, etc.)"
    echo "   + a run number (r01, r02, r03, etc.)."
    echo "   Additionally, you can then put 3 numbers as an initial"
    echo "   seed location coordinate"
    exit 1
endif

# ----- find main dset of IC
set dset_ulay = `find . -maxdepth 1 -name "${pb}.*.${run}.*.HEAD" | cut -b3-`

if ( ${#dset_ulay} == 0 ) then
    echo "** Exiting: could not find dset: ${pb}.*.${run}.*.HEAD"
    exit 1
else if ( ${#dset_ulay} == 1 ) then
    echo "++ Found IC dset: ${dset_ulay}"
    set ic_dset   = "${dset_ulay}"
else
    echo "** Exiting: too many (${#dset_ulay}) dsets: ${pb}.*.${run}.*.HEAD"
    exit 1
endif

# ----- find associated vline file, if exists
set dset_vline = ""
set dir_vline  = `find . -maxdepth 1 -type d        \\
                      -name "vlines.${pb}.*"        \\
                      | cut -b3-`
if ( ${#dir_vline} == 1 ) then
    set dset_vline  = `find ./${dir_vline} -maxdepth 1 -type f        \\
                           -name "var.1.*${run}*"                     \\
                           | cut -b3-`
endif

# ----- find associated radcor file, if exists
set dset_radcor = ""
set dir_radcor  = `find . -maxdepth 1 -type d       \\
                     -name "radcor.${pb}.*"         \\
                     | cut -b3-`
if ( ${#dir_radcor} == 1 ) then
    set dset_radcor  = `find ./${dir_radcor} -maxdepth 1 -type f     \\
                            -name "radcor.*.${run}*HEAD"             \\
                            | cut -b3-`
endif

# ----- make ordered list of dsets to load
set all_load  = ( "${dset_ulay}" "${ic_dset}"       \\
                   ${pb}*HEAD                       \\
                   ${dset_vline} ${dset_radcor}     \\
                   *.HEAD *.nii* )

# ----- finalize remaining parameters

# possible starting seed coordinate (in RAI notation)
set xcoor = "$3"
set ycoor = "$4"
set zcoor = "$5"

if ( "${zcoor}" != "" ) then
    set coord = ( "${xcoor}" "${ycoor}" "${zcoor}" )
else
    set coord = `3dinfo -dc3 "${ic_dset}"`
endif

set voxvol      = `3dinfo -voxvol "${ic_dset}"`
set ic_seedrad  = `echo "${voxvol}"                                      \\
                        | awk '{printf "%0.2f",(2*($1)^0.3334);}'`
echo "++ seedcorr radius: ${ic_seedrad}"
set ic_blur     = `echo "${voxvol}"                                      \\
                        | awk '{printf "%0.2f",(1.5*($1)^0.3334);}'`
echo "++ blurring radius: ${ic_blur}"

# ===========================================================================
# parameters set by default

setenv AFNI_ENVIRON_WARNINGS   NO
setenv AFNI_THRESH_INIT_EXPON  0
setenv AFNI_NOSPLASH           YES
setenv AFNI_SPLASH_MELT        NO
setenv AFNI_STARTUP_WARNINGS   NO
setenv AFNI_NIFTI_TYPE_WARN    NO
setenv AFNI_NO_OBLIQUE_WARNING YES
setenv AFNI_COMPRESSOR         NONE
setenv AFNI_NEVER_SAY_GOODBYE  YES
setenv AFNI_MOTD_CHECK         NO
setenv AFNI_VERSION_CHECK      NO
setenv AFNI_IMAGE_DATASETS     NO

# GUI params, set here for speed, perhaps 
setenv AFNI_DEFAULT_OPACITY    7
setenv AFNI_FUNC_BOXED         NO
setenv AFNI_THRESH_AUTO        NO

# InstaCorr parameters

set ic_ignore   = 0
set ic_blur     = ${ic_blur}           # bc the data be unprocessed
set ic_automask = no
set ic_despike  = no
set ic_bandpass = 0,99999
set ic_polort   = 3                    # bc the data be unprocessed
set ic_method   = P

# GUI visualization parameters

set pbar_sign   = "-"
set ncolors     = 99
set topval      = 0.6
set cbar        = "Reds_and_Blues_Inv"
set olay_alpha  = "Quadratic"
set thresh      = 0.3
set frange      = ${topval}
set crossh      = MULTI
set xh_gap      = -1
set OW          = "OPEN_WINDOW"

# port communication
set portnum = `afni -available_npb_quiet`

# ===========================================================================

afni -q  -no_detach                                                     \\
    -npb ${portnum}                                                     \\
     -com "SWITCH_UNDERLAY    ${dset_ulay}"                             \\
     -com "INSTACORR INIT                                               \\
                     DSET=${ic_dset}                                    \\
                   IGNORE=${ic_ignore}                                  \\
                     BLUR=${ic_blur}                                    \\
                 AUTOMASK=${ic_automask}                                \\
                  DESPIKE=${ic_despike}                                 \\
                 BANDPASS=${ic_bandpass}                                \\
                   POLORT=${ic_polort}                                  \\
                  SEEDRAD=${ic_seedrad}                                 \\
                   METHOD=${ic_method}"                                 \\
     -com "INSTACORR SET      ${coord} J"                               \\
     -com "SET_THRESHNEW      ${thresh}"                                \\
     -com "SET_PBAR_ALL       ${pbar_sign}${ncolors} ${topval} ${cbar}" \\
     -com "SET_FUNC_RANGE     ${frange}"                                \\
     -com "SET_XHAIRS         ${crossh}"                                \\
     -com "SET_XHAIR_GAP      ${xh_gap}"                                \\
     -com "SET_FUNC_ALPHA     ${olay_alpha}"                            \\
     -com "$OW sagittalimage"                                           \\
     ${all_load:q}  &

sleep 1

set l = `prompt_popup -message \\
"      Run InstaCorr on AP results data\\n\\n\\
\\n\\
InstaCorr calc using : ${ic_dset}\\n\\
Initial ulay dataset : ${dset_ulay}\\n\\
\\n\\
Wait briefly for the initial correlation patterns to appear.  \\n\\
\\n\\
To use InstaCorr:\\n\\
First, hold down Ctrl+Shift. Then Left-click anywhere in  \\n\\
the dataset, and even drag the cursor around.\\n\\
\\n\\
Correlation patterns from each clicked seed location\\n\\
update instantly.\\n\\
\\n\\
To jump to particular coordinates:\\n\\
+ Right-click -> 'Jump to (xyz)' \\n\\
+ Enter 3 space-separated coords\\n\\
+ Right-click -> 'InstaCorr set'\\n\\
... or use standard Ctrl+Shift and Left-click.\\n\\
\\n\\
Alpha (transparent) thresholding is ON. To put boxes\\n\\
around suprathreshold voxels, click 'B' above the colorbar  \\n\\
in the GUI.\\n\\
\\n"\\
-b '          Done - Close AFNI GUI          '`


if ("$l" != "1") then
    echo "+* Warn: InstaCorr guidance message failed to open"
endif

@Quiet_Talkers -npb_val ${portnum}

cat << EOF
===========================================
++ Goodbye, and thank you for InstaCorring.

EOF
exit 0

"""

# ===========================================================================
# ===========================================================================

def make_apqc_ic_script( ):
    """Make the full text (string) of the InstaCorr script

    Parameters
    ----------
    (none)

    Return
    ------
    otxt  : str
                the tcsh-syntax string (=full script) for the InstaCorr
                run script

    """

    # start of script text, default text (above)
    otxt = text_ic_top

    # and finish, with default text (above)
    otxt+= text_ic_bot

    return otxt

def write_apqc_ic_script(pname = '' ):
    """Write out the text file of the InstaCorr script.

Parameters
----------
pname : str
    optional path name to prepend to the default filename

Return
------
okay : int
    success or not of writing file: 0 = success, else = failure

    """

    # get text of script
    otext = make_apqc_ic_script()

    # write the text file in the results directory
    ofile = ''
    if pname :
        ofile = pname + '/'
    ofile+= DEF_scriptname

    fff = open(ofile, 'w')
    fff.write(otext)
    fff.close()
    
    # make executable, a la rcr
    try: code = eval('0o755')
    except: code = eval('0755')
    try:
        os.chmod(ofile, code)
    except:
        omsg = "failed: chmod {} {}".format(code, ofile)
        print(omsg)
        return 1

    msg = '''++ Done making (executable) InstaCorr script: 
    {}
    '''.format(ofile)
    print( msg )

    return 0
