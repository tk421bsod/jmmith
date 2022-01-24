
echo "Checking for updates..."
initial="$(git rev-parse --short HEAD)"
git pull > /dev/null 2>&1
ret=$?
#try https if the initial pull failed (e.g ssh blocked)
if [ $ret != 0 ]
then
    git pull https://github.com/tk421bsod/jmmith main > /dev/null 2>&1
    ret=$?
fi
after="$(git rev-parse --short HEAD)"
if [ $ret != 0 ]
then
    echo ""
    echo "Something went wrong while checking for updates. If you've made local changes, use `git status` to view what files need to be committed."
fi

if [ "$initial" != "$after" ]
then
    echo ""
    echo "Update applied. Restarting setup..."
    sleep 1
    bash setup.sh
    exit
else
    echo ""
    echo "No updates available. Starting setup."
    sleep 1
    echo ""
fi

if [ "$1" == "update" ]
then
    update="true"
    echo "Updating Jmmith with new Maximilian components."
    echo ""
else
    update="false"
fi

if [ -f token.txt -a "$update" == "false" ]
then
    echo " ---- WARNING ---- "
    echo "It looks like you've been using an older version of setup.sh. The configuration data format has changed, so you'll need to re-enter the token and database password. Don't continue until you have those ready."
    echo "Quit setup now (using either Ctrl-C or Ctrl-Z) if you want to keep (or copy) the old data."
    echo "Jmmith will not work until this finishes."
    echo "Press Enter if you want to continue. THIS WILL DELETE THE OLD DATA."
    read -s
    echo ""
    echo "Ok, starting setup."
    sleep 1
    rm token.txt
    rm dbp.txt
    echo "Deleted old data."
    echo ""
fi

if [ -f config -a "$update" == "false" ];
then
    echo " ---- WARNING ---- "
    echo "It looks like you've already run setup.sh."
    echo "Do you want to run it again? yes/no"
    echo "Warning: This will delete Jmmith's configuration data, so you'll need to reenter the database password, token, and your user id. Don't continue unless you have all of those ready."
    echo "Quit setup now (using either Ctrl-C or Ctrl-Z) if you want to keep the old data."
    read run
    if [ ${run^^} == 'NO' ];
    then
        echo "Alright. Exiting."
        exit 1
    elif [ ${run^^} == 'YES' ];
    then
        echo "Ok, starting setup."
        sleep 1
        rm config
        echo "Deleted old data."
        echo ""
    else
        echo "You need to enter either 'yes' or 'no'."
        exit 1
    fi
fi
if [ "$update" == "false" ]
then
    echo "---- Jmmith Setup ----"
    echo "This script helps set up Jmmith. It runs Maximilian's setup script, then does a few extra steps."
fi
echo "Cloning Maximilian..."
echo ""
if [ -d maximilian ]
then
    echo "It looks like Maximilian was already cloned. Pulling changes..."
    cd maximilian
    git pull
    cd ..
else
    git clone --branch minimal https://github.com/tk421bsod/maximilian
fi
if [ "$update" == "false" ]
then
    echo ""
    echo "Running Maximilian's setup.sh... Follow the prompts it gives you."
    echo ""
    cd maximilian
    sleep 1
    bash setup.sh
    result=$?
    cd ..
    echo ""
    if [ $result != 0 ]
    then
        echo "Maximilian's setup exited unexpectedly. Try running this again."
        exit 37
    fi
fi

echo "Moving some Maximilian components here..."
cp maximilian/common.py .
cp maximilian/errorhandling.py .
cp maximilian/config .
cp maximilian/helpcommand.py .
cp maximilian/core.py .
cp maximilian/errors.py .
echo "Done."

if [ "$update" == "false" ]
then
    echo ""
    echo "Enter the ID of the channel you want to use as the jmmboard."
    read jmmboard
    echo "jmmboard_channel:$jmmboard" >> config

    echo ""
    echo "Do you want to enable the draobmmj? yes/no"
    read draobmmj_enabled
    if [ ${draobmmj_enabled^^} == "YES" ]
    then
        echo "Enter the ID of the channel you want to use as the draobmmj."
        read draobmmj
        echo "draobmmj_enabled:1" >> config
        echo "draobmmj_channel:$draobmmj" >> config
    else
        echo "draobmmj_enabled:0" >> config
        echo "Not enabling the draobmmj"
    fi

    echo "Do you want to enable custom emoji?"
    echo "Read the following carefully, as your choice will greatly affect Jmmith."
    echo "Answering 'yes' will prompt you for each custom emoji Jmmith uses."
    echo "You'll need to enter the emoji in the correct format (<:name:id>). You can get an emoji in that format by typing a backslash before its name, e.g '\:gold_jmm:' = '<:gold_jmm:38347567382657>'"
echo "Answering 'no' will make Jmmith use a predefined set of built-in emoji."
read custom_emoji
if [ ${custom_emoji^^} == "YES" ]
then
    echo ""
    echo "Enabling custom emoji."
    echo "Enter the emoji you want Jmmith to use for the jmmboard. This has to be in the format shown above."
    read jmmboardemoji
    echo "jmmboard_emoji:$jmmboardemoji" >> config
    sed -i 's/custom_emoji:0/custom_emoji:1/' test
    if [ ${draobmmj_enabled^^} == "YES" ]
    then
        echo "One more thing: Enter the emoji you want Jmmith to use for the draobmmj. Again, this has to be in the format shown above."
        read draobmmj_emoji
        echo "draobmmj_emoji:$draobmmj_emoji" >> config
    else
        echo "draobmmj isn't enabled, skipping"
        echo "draobmmj_emoji:0" >> config
    fi
else
    echo ""
    echo "Disabling custom emoji."
    echo "jmmboard_emoji:0" >> config
    echo "draobmmj_emoji:0" >> config
fi

echo "Finishing database setup..."
sudo mysql maximilian -Be "CREATE TABLE jmmboard(message_id bigint); CREATE TABLE draobmmj(message_id bigint); CREATE TABLE jmmboardconfig(guild_id bigint, setting text, enabled tinyint); CREATE TABLE blocked(user_id bigint);"
echo "Cleaning up..."
rm -rf maximilian
echo "Done. Try running main.py. If you want Jmmith to work in threads, install discord.py 2.0 (instructions are at https://github.com/rapptz/discord.py/blob/master/README.rst)"
else
rm -rf maximilian
fi
