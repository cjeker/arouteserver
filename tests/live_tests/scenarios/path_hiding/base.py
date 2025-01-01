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
from packaging import version

from pierky.arouteserver.builder import OpenBGPDConfigBuilder, BIRDConfigBuilder
from pierky.arouteserver.tests.live_tests.base import LiveScenario, \
                                                      LiveScenario_TagRejectPolicy
from pierky.arouteserver.tests.live_tests.openbgpd import OpenBGPDInstance, \
                                                          OpenBGPDPortableLatestInstance

class PathHidingScenario(LiveScenario):
    __test__ = False

    MODULE_PATH = __file__
    RS_INSTANCE_CLASS = None
    CLIENT_INSTANCE_CLASS = None
    CONFIG_BUILDER_CLASS = None
    TARGET_VERSION = None

    CFG_GENERAL = None

    AS_SET = {
    }
    R_SET = {
    }

    @classmethod
    def _setup_instances(cls):
        cls.INSTANCES = [
            cls._setup_rs_instance(),

            cls.CLIENT_INSTANCE_CLASS(
                "AS1",
                cls.DATA["AS1_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS1.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS2",
                cls.DATA["AS2_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS2.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS3",
                cls.DATA["AS3_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS3.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS4",
                cls.DATA["AS4_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS4.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
            cls.CLIENT_INSTANCE_CLASS(
                "AS101",
                cls.DATA["AS101_IPAddress"],
                [
                    (
                        cls.build_other_cfg("AS101.j2"),
                        "/etc/bird/bird.conf"
                    )
                ]
            ),
        ]

    def set_instance_variables(self):
        self.rs = self._get_instance_by_name("rs")
        self.AS1 = self._get_instance_by_name("AS1")
        self.AS2 = self._get_instance_by_name("AS2")
        self.AS3 = self._get_instance_by_name("AS3")
        self.AS4 = self._get_instance_by_name("AS4")
        self.AS101 = self._get_instance_by_name("AS101")

    def test_010_setup(self):
        """{}: instances setup"""
        pass

    def test_020_sessions_up(self):
        """{}: sessions are up"""
        self.session_is_up(self.rs, self.AS1)
        self.session_is_up(self.rs, self.AS2)
        self.session_is_up(self.rs, self.AS3)
        self.session_is_up(self.rs, self.AS4)
        self.session_is_up(self.AS1, self.AS101)
        self.session_is_up(self.AS2, self.AS101)

    def test_030_rs_receives_route_from_AS1_and_AS2(self):
        """{}: rs should receive prefix from both AS1 and AS2"""
        self.receive_route(self.rs, self.DATA["AS101_pref_ok1"], self.AS1,
                           as_path="1 101")
        self.receive_route(self.rs, self.DATA["AS101_pref_ok1"], self.AS2,
                           as_path="2 101 101 101 101")

    def test_031_rs_has_best_toward_AS1(self):
        """{}: rs should have best toward AS1"""
        self.receive_route(self.rs, self.DATA["AS101_pref_ok1"], self.AS1,
                           only_best=True)

    def test_032_AS1_do_not_announce_to_AS3_and_AS4(self):
        """{}: AS1 wants rs to not announce to AS3 and AS4"""
        self.receive_route(self.rs, self.DATA["AS101_pref_ok1"], self.AS1,
                           std_comms=["0:3", "0:4"])
        self.log_contains(self.rs, "route didn't pass control communities checks - NOT ANNOUNCING {} TO {{AS3}}".format(
            self.DATA["AS101_pref_ok1"]), {"AS3": self.AS3})
        self.log_contains(self.rs, "route didn't pass control communities checks - NOT ANNOUNCING {} TO {{AS4}}".format(
            self.DATA["AS101_pref_ok1"]), {"AS4": self.AS4})

    def test_900_reconfigure(self):
        """{}: reconfigure"""
        self.rs.reload_config()
        self.test_020_sessions_up()

class PathHidingScenarioBIRD(PathHidingScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = BIRDConfigBuilder
    IP_VER = None

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("bird", "main.j2", "rs.conf", cls.IP_VER,
                                     cfg_general=cls.CFG_GENERAL,
                                     target_version=cls.TARGET_VERSION or cls.RS_INSTANCE_CLASS.TARGET_VERSION),
                    "/etc/bird/bird.conf"
                )
            ]
        )

class PathHidingScenarioBIRD2(PathHidingScenarioBIRD):
    __test__ = False

class PathHidingScenarioBIRD3(PathHidingScenarioBIRD):
    __test__ = False

class PathHidingScenarioOpenBGPD(LiveScenario_TagRejectPolicy, PathHidingScenario):
    __test__ = False

    CONFIG_BUILDER_CLASS = OpenBGPDConfigBuilder

    @classmethod
    def _setup_rs_instance(cls):
        return cls.RS_INSTANCE_CLASS(
            "rs",
            cls.DATA["rs_IPAddress"],
            [
                (
                    cls.build_rs_cfg("openbgpd", "main.j2", "rs.conf", None,
                                     cfg_general=cls._get_cfg_general(cls.CFG_GENERAL),
                                     target_version=cls.TARGET_VERSION or cls.RS_INSTANCE_CLASS.TARGET_VERSION),
                    "/etc/bgpd.conf"
                )
            ]
        )

class PathHidingScenarioOpenBGPDPrevious(PathHidingScenarioOpenBGPD):
    __test__ = False

class PathHidingScenarioOpenBGPDLatest(PathHidingScenarioOpenBGPD):
    __test__ = False

class PathHidingScenario_MitigationOn(object):

    CFG_GENERAL = "general_on.yml"

    def test_040_AS3_and_AS4_prefix_via_AS2(self):
        """{}: AS3 and AS4 receive prefix with sub-optimal path via AS2"""
        target_version = self.TARGET_VERSION or self.RS_INSTANCE_CLASS.TARGET_VERSION

        if isinstance(self.rs, OpenBGPDInstance) and \
           version.parse(target_version.replace("p0", "")) < version.parse("6.9"):
            raise unittest.SkipTest("Path hiding mititaion not supported on OpenBGPD < 6.9")

        for inst in (self.AS3, self.AS4):
            if isinstance(self.rs, OpenBGPDInstance) and \
                version.parse(target_version) >= version.parse("7.5") and \
                version.parse(target_version) < version.parse("7.6") and \
                inst is self.AS3:
                # On OpenBGPD 7.5, ADD_PATH support was introduced: however,
                # when it is set, the 'rde evaluate all' config knob that allows
                # the BGP daemon to keep evaluating alternative paths in case
                # the selected path is filtered out cannot be turned on - bgpd
                # would generate the error
                #   neighbors with add-path send cannot use 'rde evaluate all'
                #
                # The clients in this scenario are all configured with ADD_PATH
                # send enabled, but only AS4 has it also configured on its end
                # with the rx, so AS3 would not benefit from the path hiding
                # mitigation offered when 'rde evaluate all' is set, thus it
                # would not be able to receive the route.
                with self.assertRaisesRegex(AssertionError, "Routes not found."):
                    self.receive_route(inst, self.DATA["AS101_pref_ok1"], self.rs)
            else:
                self.receive_route(inst, self.DATA["AS101_pref_ok1"], self.rs,
                                as_path="2 101 101 101 101", next_hop=self.AS2,
                                std_comms=[])

    def test_041_AS3_and_AS4_no_prefix_via_AS1(self):
        """{}: AS3 and AS4 don't receive prefix via AS1"""
        for inst in (self.AS3, self.AS4):
            with self.assertRaisesRegex(AssertionError, "Routes not found."):
                self.receive_route(inst, self.DATA["AS101_pref_ok1"], self.rs,
                                   next_hop=self.AS1)

    def test_061_2nd_best_withdrawn(self):
        """{}: 2nd best is withdrawn and AS3 should not see it anymore"""

        if not isinstance(self.rs, OpenBGPDPortableLatestInstance):
            raise unittest.SkipTest("OpenBSD version not patched")

        # Details on:
        # https://github.com/openbgpd-portable/openbgpd-portable/issues/21#

        self.AS101._birdcl("disable AS2")

        self.rs.clear_cached_routes()
        self.receive_route(self.rs, self.DATA["AS101_pref_ok1"], self.AS1,
                           as_path="1 101")

        self.AS3.clear_cached_routes()
        with self.assertRaisesRegex(AssertionError, "Routes not found."):
            self.receive_route(self.AS3, self.DATA["AS101_pref_ok1"])

class PathHidingScenario_MitigationOff(object):

    CFG_GENERAL = "general_off.yml"

    def test_050_AS3_prefix_not_received_by_AS3(self):
        """{}: AS3 does not receive prefix at all"""
        with self.assertRaisesRegex(AssertionError, "Routes not found."):
            self.receive_route(self.AS3, self.DATA["AS101_pref_ok1"])

    def test_051_AS4_receives_prefix_via_AS2_because_of_ADD_PATH(self):
        """{}: AS4 receives the prefix via AS2 because of ADD-PATH"""
        if isinstance(self.rs, OpenBGPDInstance):
            if version.parse(self.rs.TARGET_VERSION) < version.parse("7.5"):
                raise unittest.SkipTest("ADD-PATH not supported by OpenBGPD < 7.5")

        self.receive_route(self.AS4, self.DATA["AS101_pref_ok1"], self.rs,
                           as_path="2 101 101 101 101", next_hop=self.AS2,
                           std_comms=[])
