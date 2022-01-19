if [ -f token.txt ]
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

if [ -f config ];
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

echo "---- Jmmith Setup ----"
echo "This script helps set up Jmmith. It runs Maximilian's setup script, then does a few extra steps."
echo "Cloning Maximilian..."
echo ""
if [ -d maximilian ]
then
    echo "It looks like Maximilian was already cloned. Pulling changes..."
    cd maximilian
    git pull
    cd ..
else
    git clone https://github.com/tk421bsod/maximilian
fi
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
echo "Moving some Maximilian components here..."
cp maximilian/common.py .
cp maximilian/errorhandling.py .
cp maximilian/config .
cp maximilian/helpcommand.py .
cp maximilian/core.py .
cp maximilian/errors.py .
echo "Finishing database setup..."
sudo mysql maximilian -Be "CREATE TABLE jmmboard(message_id bigint); CREATE TABLE draobmmj(message_id bigint); CREATE TABLE jmmboardconfig(guild_id bigint, setting text, enabled tinyint);"
echo "Cleaning up..."
rm -rf maximilian
echo "Done. Try running main.py. If you want Jmmith to work in threads, install discord.py 2.0 (instructions are at https://github.com/rapptz/discord.py/blob/master/README.rst)"
