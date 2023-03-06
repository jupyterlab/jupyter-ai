# script that bumps version for all projects regardless of whether they were
# changed since last release. needed because `lerna version` only bumps versions for projects
# listed by `lerna changed` by default.
#
# see: https://github.com/lerna/lerna/issues/2369

root_package=../..

for package in ../*; do
    touch $package/TEMP && git add $package/TEMP
done
touch $root_package/TEMP && git add $root_package/TEMP

(npx -p lerna -y lerna version --no-git-tag-version --no-push -y $1) || exit 1

for package in ../*; do
    git rm -f $package/TEMP
done
git rm -f $root_package/TEMP
