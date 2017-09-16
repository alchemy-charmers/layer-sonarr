# Overview

This charm provides [Sonarr][sonarr]. Sonarr is an automatic NZB
downloader for tv shows, written in python.

# Usage

To deploy:

    juju deploy cs:~chris.sanders/sonarr

This charm implements 
 * [interface:reverseproxy][interface-reverseproxy] intended for use with the 
   [HAProxy Charm][charm-haproxy]. This should be used if remote access is required 
   to enable TLS encryption. 
 * [interface:usenetdownloader][interface-usenetdownloader] intended for use
   with the [Sabnzbd Charm][charm-sabnzbd].  

## Known Limitations and Issues

This charm is under development, several other use cases/features are still under
consideration. Merge requests are certainly appreciated, some examples of
current limitations include.

 * Scale out usage is not intended, I'm not even sure what use it would be.
 * Unit/Functional testing is not yet implemented

# Configuration
You will most likely want to use a bundle to set options during deployment. 

See the full list of configuration options below. This will detail some of the
options that are worth highlighting.

 - restore-config: Combined with a resource allows restoring a previous
   configuration. This can also be used to migrate from non-charmed
   sonarr. The sonarr backup zip needs to be attached as the resource sonarrconfig. 
 - backup-count: This configuration is not used.
 - backup-location: A folder to sync the Sonarr backups to daily, number and
   frequency of backups are controlled by Sonarr. This charm simply syncs
   (including deletions) the Backup folder to another location of your choosing.
 - proxy-*: The proxy settings allow configuration of the reverseproxy interface
   that will be registered during relation.
 - hostname will allow you to customize the hostname, be aware that
   doing this can cause multiple hosts to have the same hostname if you scale
   out the number of units. Setting hostname to "$UNIT" will set the hostname to
   the juju unit id. Note scaling out is not supported, tested, or useful.

# Contact Information

## Upstream Project Information

  - Code: https://github.com/chris-sanders/layer-sonarr 
  - Bug tracking: https://github.com/chris-sanders/layer-sonarr/issues
  - Contact information: sanders.chris@gmail.com

[sonarr]: https://sonarr.tv/
[charm-haproxy]: https://jujucharms.com/u/chris.sanders/haproxy
[charm-sabnzbd]: https://jujucharms.com/u/chris.sanders/sabnzbd
[interface-reverseproxy]: https://github.com/chris-sanders/interface-reverseproxy
[interface-usenetdownloader]: https://github.com/chris-sanders/interface-usenet-downloader

