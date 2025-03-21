# Copyright (C) 2017-2025 Pier Carlo Chiodi
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import unittest

import yaml

from .cfg_base import TestConfigParserBase
from pierky.arouteserver.config.clients import ConfigParserClients
from pierky.arouteserver.config.general import ConfigParserGeneral


class TestConfigParserClients(TestConfigParserBase):

    FILE_PATH = "config.d/clients.yml"
    CONFIG_PARSER_CLASS = ConfigParserClients
    SHORT_DESCR = "Clients config parser"

    def test_valid_cfg(self):
        """{}: valid configuration"""
        self._contains_err()

    def test_unknown_statement(self):
        """{}: unknown statement"""
        self.cfg[0]["test"] = "test"
        self._contains_err("Unknown statement at 'clients' level: 'test'.")

    def test_as(self):
        """{}: AS number"""
        for v in (-1, 0, "test"):
            self.cfg[0]["asn"] = v
            self._contains_err("Error parsing 'asn' at 'clients' level - Invalid ASN: {}.".format(v))

    def test_ip(self):
        """{}: IP address"""
        for v in ("192.0.2.1/24", "2001:db8::1/64"):
            self.cfg[0]["ip"] = v
            self._contains_err("Error parsing 'ip' at 'clients' level - Invalid IP address: {}.".format(v))
        for v in ("192.0.2.1", "10.0.1.1", "1.2.3.4", "fe80::1", "2001:DB8::1"):
            self.cfg[0]["ip"] = v
            self._contains_err()

    def test_duplicate_ip(self):
        """{}: duplicate IP addresses"""
        self.cfg[0]["ip"] = "192.0.2.1"
        self.cfg[1]["ip"] = self.cfg[0]["ip"]
        self._contains_err("Duplicate IP address found: 192.0.2.1.")

    def test_no_ip(self):
        """{}: no IP addresses"""
        self.cfg[0]["ip"] = None
        self._contains_err("Error parsing 'ip' at 'clients' level - Can't be empty.")
        self._contains_err("One or more errors occurred while processing the client configuration for 'AS3333'")

    def test_next_hop_policy_no_authorized_addresses_with_list(self):
        """{}: next_hop.policy != authorized_addresses, list given"""
        self.cfg[0]["cfg"]["filtering"]["next_hop"]["policy"] = "strict"
        self.cfg[0]["cfg"]["filtering"]["next_hop"]["authorized_addresses_list"] = ["192.168.0.1"]
        self._contains_err("AS3333 192.0.2.11 is not 'authorized_addresses' but the 'authorized_addresses_list' option is set")

    def test_next_hop_policy_authorized_addresses_empty(self):
        """{}: next_hop.policy authorized_addresses, empty list"""
        self.cfg[0]["cfg"]["filtering"]["next_hop"]["policy"] = "authorized_addresses"
        self._contains_err("set to 'authorized_addresses' but the list of authorized IP addresses ('authorized_addresses_list') is empty")

    def test_next_hop_policy_authorized_addresses_invalid(self):
        """{}: next_hop.policy authorized_addresses, invalid list"""
        self.cfg[0]["cfg"]["filtering"]["next_hop"]["policy"] = "authorized_addresses"
        self.cfg[0]["cfg"]["filtering"]["next_hop"]["authorized_addresses_list"] = "test"
        self._contains_err("Error parsing 'authorized_addresses_list' at 'clients.cfg.filtering.next_hop' level - Invalid format: must be a list.")

    def test_next_hop_policy_authorized_addresses_invalid_address(self):
        """{}: next_hop.policy authorized_addresses, invalid IP addr"""
        self.cfg[0]["cfg"]["filtering"]["next_hop"]["policy"] = "authorized_addresses"
        self.cfg[0]["cfg"]["filtering"]["next_hop"]["authorized_addresses_list"] = ["test"]
        self._contains_err("Error parsing 'authorized_addresses_list' at 'clients.cfg.filtering.next_hop' level - Invalid IP address: test.")

    def test_next_hop_policy_both(self):
        """{}: next_hop.policy and next_hop_policy"""
        self.cfg[0]["cfg"]["filtering"]["next_hop_policy"] = "strict"
        self.cfg[0]["cfg"]["filtering"]["next_hop"]["policy"] = "authorized_addresses"
        self.cfg[0]["cfg"]["filtering"]["next_hop"]["authorized_addresses_list"] = ["test"]
        self._contains_err("Can't use the new 'next_hop' and the old 'next_hop_policy' statements simultaneously")

    def test_next_hop_policy_authorized_addresses_ok(self):
        """{}: next_hop.policy authorized_addresses, ok"""
        self.cfg[0]["cfg"]["filtering"]["next_hop"]["policy"] = "authorized_addresses"
        self.cfg[0]["cfg"]["filtering"]["next_hop"]["authorized_addresses_list"] = ["192.168.0.1"]
        self._contains_err()

    def test_multiple_ip_addresses(self):
        """{}: clients with multiple IP addresses"""
        clients_config = [
            "clients:",
            "  - asn: 111",
            "    ip:",
            "      - '192.0.2.11'",
            "      - '2001:db8:1:1::11'",
            "  - asn: 222",
            "    ip:",
            "      - '192.0.2.21'",
            "      - '2001:db8:1:1::21'",
        ]

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join(clients_config))
        self._contains_err()

        # Duplicate address.
        clients_config = [
            "clients:",
            "  - asn: 111",
            "    ip:",
            "      - '192.0.2.11'",
            "      - '2001:db8:1:1::11'",
            "  - asn: 222",
            "    ip:",
            "      - '192.0.2.11'",
            "      - '2001:db8:1:1::21'",
        ]

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join(clients_config))
        self._contains_err("Duplicate IP address found: 192.0.2.11")

    def test_inherit_from_general_cfg(self):
        """{}: inherit from general cfg"""
        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2"
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join([
            "clients:",
            "  - asn: 111",
            "    ip: 192.0.2.11",
            "  - asn: 222",
            "    ip: 192.0.2.21",
            "    cfg:",
            "      passive: False",
            "      prepend_rs_as: True",
            "      add_path: True",
            "      rfc8950: True",
            "      filtering:",
            "        irrdb:",
            "          enforce_origin_in_as_set: False",
            "          enforce_prefix_in_as_set: False",
            "          white_list_pref:",
            "            - prefix: 192.0.2.0",
            "              length: 24",
            "          white_list_asn:",
            "            - 11",
            "            - 12",
            "          white_list_route:",
            "            - prefix: 192.0.2.0",
            "              length: 24",
            "              le: 32",
            "              asn: 65534",
            "        rpki_bgp_origin_validation:",
            "          enabled: True",
            "          reject_invalid: False",
            "        reject_invalid_as_in_as_path: False",
            "        max_as_path_len: 64",
            "        ipv4_pref_len:",
            "          min: 1",
            "          max: 2",
            "        ipv6_pref_len:",
            "          min: 3",
            "          max: 4",
            "        # test pre v0.6.0 format for next_hop",
            "        next_hop_policy: same-as",
            "        max_prefix:",
            "          # test pre v0.13.0 format for peering_db",
            "          peering_db: False",
            "          limit_ipv4: 10",
            "          limit_ipv6: 20",
            "        reject_policy:",
            "          policy: tag",
            "      graceful_shutdown:",
            "        enabled: True",
            "  - asn: 333",
            "    ip: 192.0.2.31",
            "    cfg:",
            "      filtering:",
            "        next_hop:",
            "          policy: 'authorized_addresses'",
            "          authorized_addresses_list:",
            "            - '192.0.2.31'",
            "            - '192.0.2.32'",
            "            - '2001:db8:0:0::31'",
            "        irrdb:",
            "          # testing optional ASN",
            "          white_list_route:",
            "            - prefix: 192.0.2.0",
            "              length: 24",
            "              le: 32"
        ]))
        self.cfg.parse()
        self._contains_err()

        client = self.cfg[0]
        self.assertEqual(client["cfg"]["passive"], True)
        self.assertEqual(client["cfg"]["add_path"], False)
        self.assertEqual(client["cfg"]["rfc8950"], False)
        self.assertEqual(client["cfg"]["prepend_rs_as"], False)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["enforce_origin_in_as_set"], True)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["enforce_prefix_in_as_set"], True)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_pref"], None)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_asn"], None)
        self.assertEqual(client["cfg"]["filtering"]["rpki_bgp_origin_validation"]["enabled"], False)
        self.assertEqual(client["cfg"]["filtering"]["rpki_bgp_origin_validation"]["reject_invalid"], True)
        self.assertEqual(client["cfg"]["filtering"]["reject_invalid_as_in_as_path"], True)
        self.assertEqual(client["cfg"]["filtering"]["max_as_path_len"], 32)
        self.assertEqual(client["cfg"]["filtering"]["ipv4_pref_len"]["min"], 8)
        self.assertEqual(client["cfg"]["filtering"]["ipv4_pref_len"]["max"], 24)
        self.assertEqual(client["cfg"]["filtering"]["ipv6_pref_len"]["min"], 12)
        self.assertEqual(client["cfg"]["filtering"]["ipv6_pref_len"]["max"], 48)
        self.assertEqual(client["cfg"]["filtering"]["next_hop"]["policy"], "strict")
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["limit_ipv4"], None)
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["limit_ipv6"], None)
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["peering_db"]["enabled"], True)
        self.assertEqual(client["cfg"]["filtering"]["reject_policy"]["policy"], "reject")

        client = self.cfg[1]
        self.assertEqual(client["cfg"]["passive"], False)
        self.assertEqual(client["cfg"]["add_path"], True)
        self.assertEqual(client["cfg"]["rfc8950"], True)
        self.assertEqual(client["cfg"]["prepend_rs_as"], True)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["enforce_origin_in_as_set"], False)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["enforce_prefix_in_as_set"], False)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_pref"][0]["prefix"], "192.0.2.0")
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_pref"][0]["length"], 24)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_asn"], [11, 12])
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_route"][0]["prefix"], "192.0.2.0")
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_route"][0]["length"], 24)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_route"][0]["le"], 32)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_route"][0]["asn"], 65534)
        self.assertEqual(client["cfg"]["filtering"]["rpki_bgp_origin_validation"]["enabled"], True)
        self.assertEqual(client["cfg"]["filtering"]["rpki_bgp_origin_validation"]["reject_invalid"], False)
        self.assertEqual(client["cfg"]["filtering"]["reject_invalid_as_in_as_path"], False)
        self.assertEqual(client["cfg"]["filtering"]["max_as_path_len"], 64)
        self.assertEqual(client["cfg"]["filtering"]["ipv4_pref_len"]["min"], 1)
        self.assertEqual(client["cfg"]["filtering"]["ipv4_pref_len"]["max"], 2)
        self.assertEqual(client["cfg"]["filtering"]["ipv6_pref_len"]["min"], 3)
        self.assertEqual(client["cfg"]["filtering"]["ipv6_pref_len"]["max"], 4)
        self.assertEqual(client["cfg"]["filtering"]["next_hop"]["policy"], "same-as")
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["limit_ipv4"], 10)
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["limit_ipv6"], 20)
        self.assertEqual(client["cfg"]["filtering"]["max_prefix"]["peering_db"]["enabled"], False)
        self.assertEqual(client["cfg"]["filtering"]["reject_policy"]["policy"], "tag")
        self.assertEqual(client["cfg"]["graceful_shutdown"]["enabled"], True)

        client = self.cfg[2]
        self.assertEqual(client["cfg"]["filtering"]["next_hop"]["policy"], "authorized_addresses")
        self.assertEqual(client["cfg"]["filtering"]["next_hop"]["authorized_addresses_list"], [
            "192.0.2.31", "192.0.2.32", "2001:db8:0:0::31"
        ])
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_route"][0]["prefix"], "192.0.2.0")
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_route"][0]["length"], 24)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_route"][0]["le"], 32)
        self.assertEqual(client["cfg"]["filtering"]["irrdb"]["white_list_route"][0]["asn"], None)

    def test_blackhole_filtering_propagation(self):
        """{}: inherit from general cfg - blackhole filtering"""
        clients_config = [
            "clients:",
            "  - asn: 111",
            "    ip: 192.0.2.11",
            "    cfg:",
            "      blackhole_filtering:",
            "  - asn: 222",
            "    ip: 192.0.2.21",
            "    cfg:",
            "      blackhole_filtering:",
            "        announce_to_client: True",
            "  - asn: 333",
            "    ip: 192.0.2.31",
            "    cfg:",
            "      blackhole_filtering:",
            "        announce_to_client: False",
        ]

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join(clients_config))
        self.cfg.parse()
        self._contains_err()

        self.assertIs(general["blackhole_filtering"]["announce_to_client"], True)

        client = self.cfg[0]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], True)
        client = self.cfg[1]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], True)
        client = self.cfg[2]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], False)

        # ------------------------

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  blackhole_filtering:",
            "    announce_to_client: False"
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join(clients_config))
        self.cfg.parse()
        self._contains_err()

        self.assertTrue(general["blackhole_filtering"]["announce_to_client"] is False)

        client = self.cfg[0]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], False)
        client = self.cfg[1]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], True)
        client = self.cfg[2]
        self.assertIs(client["cfg"]["blackhole_filtering"]["announce_to_client"], False)

    def test_custom_bgp_communities_ok(self):
        """{}: custom BGP communities"""
        clients_config = [
            "clients:",
            "  - asn: 111",
            "    ip: 192.0.2.11",
            "  - asn: 222",
            "    ip: 192.0.2.21",
            "    cfg:",
            "      attach_custom_communities:"
        ]
        yaml_lines = clients_config + [
            "        - test1",
            "        - test2",
        ]

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
            "  custom_communities:",
            "    test1:",
            "      std: '1:1'"
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join(yaml_lines))
        self._contains_err("The custom BGP community test2 referenced on client AS222 192.0.2.21 is not declared on the general configuration.")

        yaml_lines = clients_config + [
            "        - test1",
        ]
        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join(yaml_lines))
        self._contains_err()

    def test_global_only_option(self):
        """{}: global only option"""
        clients_config = [
            "clients:",
            "  - asn: 222",
            "    ip: 192.0.2.21",
            "    cfg:",
            "      filtering:",
            "        irrdb:",
            "          allow_longer_prefixes: True"
        ]

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2",
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join(clients_config))
        self._contains_err("Unknown statement at 'clients.cfg.filtering.irrdb' level: 'allow_longer_prefixes'")

    def test_custom_options_ok(self):
        """{}: custom_options"""

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2"
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join([
            "clients:",
            "  - asn: 222",
            "    ip: 192.0.2.21",
            "    cfg:",
            "      custom_options:",
            "        bird:",
            "          ipv4:",
            "            channel:",
            "              config_lines:",
            "                - AA",
            "                - BB",
            "          ipv6:",
            "            protocol:",
            "              config_lines:",
            "                - AA",
            "                - BB",
            "          any:",
            "            channel:",
            "              config_lines:",
            "                - AA",
            "                - BB",
            "        openbgpd:",
            "          ipv4:",
            "            client:",
            "              config_lines:",
            "                - AA",
            "                - BB",
        ]))
        self.cfg.parse()
        self._contains_err()

        client = self.cfg[0]
        self.assertEqual(client["cfg"]["custom_options"]["bird"]["ipv4"]["channel"]["config_lines"][0], "AA")

    def test_custom_options_bad_format(self):
        """{}: custom_options - bad format"""

        self.cfg[0]["cfg"]["custom_options"] = 1
        self._contains_err("Invalid format for custom_options: must be a dictionary.")

    def test_custom_options_bad_bgp_speaker(self):
        """{}: custom_options - bad BGP speaker"""

        self.cfg[0]["cfg"]["custom_options"] = {"A": 1}
        self._contains_err("Unknown BGP speaker: A. Must be one of bird, openbgpd.")

    def test_custom_options_bad_bgp_speaker_fmt(self):
        """{}: custom_options - bad BGP speaker format"""

        self.cfg[0]["cfg"]["custom_options"] = {"bird": "A"}
        self._contains_err(
            "Unknown AF in custom_options.bird: A. Must be one of ipv4, ipv6, any."
        )

    def test_custom_options_bad_af_value(self):
        """{}: custom_options - bad AF"""

        self.cfg[0]["cfg"]["custom_options"] = {"bird": {"A": ""}}
        self._contains_err(
            "Unknown AF in custom_options.bird: A. Must be one of ipv4, ipv6, any."
        )

    def test_custom_options_bad_af_fmt(self):
        """{}: custom_options - bad AF format"""

        self.cfg[0]["cfg"]["custom_options"] = {"bird": {"ipv4": "A"}}
        self._contains_err(
            "Unknown format custom_options.bird.ipv4: must be a dict."
        )

    def test_custom_options_bad_section_bird(self):
        """{}: custom_options - bad section"""

        self.cfg[0]["cfg"]["custom_options"] = {"bird": {"ipv4": {"A": "B"}}}
        self._contains_err(
            "Unknown section in custom_options.bird.ipv4: A. "
            "For bird, it must be one of protocol, channel."
        )

    def test_custom_options_missing_section(self):
        """{}: custom_options - missing section"""

        self.cfg[0]["cfg"]["custom_options"] = {"bird": {"ipv4": {}}}
        self._contains_err(
            "Missing section in custom_options.bird.ipv4. For bird, it must be one of protocol, channel."
        )


    def test_custom_options_bad_option(self):
        """{}: custom_options - bad option"""

        self.cfg[0]["cfg"]["custom_options"] = {"bird": {"ipv4": {"channel": {"A": "B"}}}}
        self._contains_err(
            "Unknown format for custom_options.bird.ipv4.channel: at the moment the "
            "only supported key is config_lines, a list of custom configuration "
            "lines specific to the BGP speaker."
        )

    def test_custom_options_missing_options(self):
        """{}: custom_options - missing options"""

        self.cfg[0]["cfg"]["custom_options"] = {"bird": {"ipv4": {"protocol": {}}}}
        self._contains_err(
            "Unknown format for custom_options.bird.ipv4.protocol: at the moment the "
            "only supported key is config_lines, a list of custom configuration "
            "lines specific to the BGP speaker."
        )

    def test_16bit_mapped_asn(self):
        """{}: 16bit_mapped_asn"""
        self.assertEqual(self.cfg.asn3216_map, {65551: 64512})

    def test_16bit_mapped_asn_not_a_32bit_asn(self):
        """{}: 16bit_mapped_asn for a 16bit ASN"""
        self.cfg[0]["16bit_mapped_asn"] = 64512
        self._contains_err(
            "The '16bit_mapped_asn' option can be set only for 32bit ASNs, "
            "but it was set for the 16bit ASN client AS3333 192.0.2.11"
        )

    def test_16bit_mapped_asn_not_a_16bit_asn(self):
        """{}: 16bit_mapped_asn not in valid range"""
        self.cfg[3]["16bit_mapped_asn"] = 3
        self._contains_err(
            "Error parsing '16bit_mapped_asn' at 'clients' level - Invalid private 16bit ASN: 3."
        )

    def test_16bit_mapped_asn_reused_16bit(self):
        """{}: 16bit_mapped_asn re-used for another ASN"""

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2"
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join([
            "clients:",
            "  - asn: 65550",
            "    ip: 192.0.2.21",
            "    16bit_mapped_asn: 64512",
            "  - asn: 65551",
            "    ip: 192.0.2.22",
            "    16bit_mapped_asn: 64512",
        ]))
        self._contains_err(
            "The 16bit ASN 64512 was used for the '16bit_mapped_asn' option "
            "of client AS65551 192.0.2.22, but previously it was already used "
            "to map the 32bit ASN 65550 of another client"
        )

    def test_16bit_mapped_asn_different_16bit_for_same_32bit(self):
        """{}: 16bit_mapped_asn different 16bit for the same 32bit"""

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2"
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join([
            "clients:",
            "  - asn: 65550",
            "    ip: 192.0.2.21",
            "    16bit_mapped_asn: 64512",
            "  - asn: 65550",
            "    ip: 192.0.2.22",
            "    16bit_mapped_asn: 65534",
        ]))
        self._contains_err(
            "The '16bit_mapped_asn' option of client AS65550 192.0.2.22 "
            "was set to 65534, but previously another 16bit ASN was "
            "already used for that ASN: 64512"
        )

    def test_16bit_mapped_asn_combo(self):
        """{}: 16bit_mapped_asn combo"""

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2"
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join([
            "clients:",
            "  - asn: 65550",
            "    ip: 192.0.2.21",
            "    16bit_mapped_asn: 64512",
            "  - asn: 65551",
            "    ip: 192.0.2.22",
            "    16bit_mapped_asn: 65534",
        ]))
        self.cfg.parse()
        self.assertEqual(self.cfg.asn3216_map, {65550: 64512, 65551: 65534})

    def test_16bit_mapped_asn_same_as_multiple_client_definitions(self):
        """{}: 16bit_mapped_asn same AS multiple clients"""

        general = ConfigParserGeneral()
        general._load_from_yaml("\n".join([
            "cfg:",
            "  rs_as: 999",
            "  router_id: 192.0.2.2"
        ]))
        general.parse()

        self.cfg = ConfigParserClients(general_cfg=general)
        self.cfg._load_from_yaml("\n".join([
            "clients:",
            "  - asn: 65550",
            "    ip: 192.0.2.21",
            "    16bit_mapped_asn: 64512",
            "  - asn: 65550",
            "    ip: 192.0.2.22",
            "    16bit_mapped_asn: 64512",
        ]))
        self.cfg.parse()
        self.assertEqual(self.cfg.asn3216_map, {65550: 64512})
