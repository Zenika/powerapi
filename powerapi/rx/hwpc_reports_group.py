# Copyright (c) 2022, INRIA
# Copyright (c) 2022, University of Lille
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holder nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# Author : Daniel Romero Acero
# Last modified : 18 mai 2022

##############################
#
# Imports
#
##############################
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any

from powerapi.exception import BadInputDataException
from powerapi.rx import Report
from powerapi.rx.report import TARGET_CN
from powerapi.rx.reports_group import ReportsGroup, TIMESTAMP_CN, SENSOR_CN, METADATA_CN

##############################
#
# Constants
#
##############################

GROUPS_CN = "groups"
SOCKET_CN = "socket_id"
CORE_CN = "core_id"
EVENT_CN = "event_id"
EVENT_VALUE_CN = "event_value"

MSR_GROUP = "msr"
CORE_GROUP = "core"


##############################
#
# Classes
#
##############################


class HWPCReportsGroup(ReportsGroup):
    """ Class that enables the grouping of hwpc reports by sensor, timestamp and metadata """

    def __init__(self, timestamp: datetime, sensor: str, report: Report, metadata: Dict = {}):
        """ Initialize an empty group
            Args:
                timestamp: The timestamp of the group
                sensor: The sensor related to the group
                report: The original report. It will be used to store reports with commons basic information
                metadata: The metadata related to the group

        """
        super().__init__(timestamp=timestamp, sensor=sensor, report=report, metadata=metadata)

    def to_mongodb_dict(self) -> [Dict]:
        """ Creates a list with the dict of each report row

            Return:
                A list with a dict representation of each report row

        """
        reports_dict = []
        # We get the dictionary with the basic information
        report_dict_basics = super()._to_mongodb_dict_basic_infos()

        current_index = 0
        columns_names = self.report.columns.values

        group_by_target_dict = self.report.groupby(
            TARGET_CN, sort=False).indices  # It contains target name as key and an array of int as
        # values that are indexes on the report for rows with same target

        for current_target in group_by_target_dict.keys():
            current_report_dict = report_dict_basics  # we add the basics and the target
            current_report_dict[TARGET_CN] = current_target
            current_report_dict[GROUPS_CN] = {}
            for current_row_index in group_by_target_dict[current_target]:
                current_row = self.report.iloc[current_row_index]
                group_id = current_row[GROUPS_CN]
                socket_id = current_row[SOCKET_CN]
                core_id = current_row[CORE_CN]
                event_id = current_row[EVENT_CN]
                event_value = current_row[EVENT_VALUE_CN]

                if group_id not in current_report_dict[GROUPS_CN]:  # We create the group
                    current_report_dict[GROUPS_CN][group_id] = {}

                if socket_id not in current_report_dict[GROUPS_CN][group_id]:  # We create the subgroup
                    current_report_dict[GROUPS_CN][group_id][socket_id] = {}

                if core_id not in current_report_dict[GROUPS_CN][group_id][socket_id]:  # We create the subgroup
                    current_report_dict[GROUPS_CN][group_id][socket_id][core_id] = {}

                # We add the event value
                current_report_dict[GROUPS_CN][group_id][socket_id][core_id][event_id] = event_value

            reports_dict.append(current_report_dict)

        return reports_dict

    @staticmethod
    def create_reports_group_from_dicts(reports_dict: [Dict[str, Any]]):
        """ Creates a group report by using the given information

            All the dictionaries have the same timestamp, sensor and metadata
            Args:
                reports_dict: List of dictionaries that contains information of the report
            Return :
                A new group report created using information contained in the list of dictionaries
        """
        # We check that all the required information is in the input dictionary
        if not HWPCReportsGroup.is_information_in_reports_dict(reports_dict):
            raise BadInputDataException(
                msg=f"One of the following infos is missing in at least one of the input dictionaries: {TIMESTAMP_CN}, "
                    f"{SENSOR_CN}, "
                    f"{TARGET_CN}, "
                    f"{GROUPS_CN}. The HWPCReportsGroup cannot be created", input_data=reports_dict)

        # We create the report
        report_data_dict = {TARGET_CN: [], GROUPS_CN: [], SOCKET_CN: [], CORE_CN: [], EVENT_CN: [], EVENT_VALUE_CN: []}

        for current_report_dict in reports_dict:
            current_groups_dict = current_report_dict[GROUPS_CN]
            current_target = current_report_dict[TARGET_CN]
            for current_group_id, current_sockets_dict in current_groups_dict.items():
                for current_socket_id, current_cores_dict in current_sockets_dict.items():
                    for current_core_id, current_events_dict in current_cores_dict.items():
                        for current_event_id, current_event_value in current_events_dict.items():
                            # We add a line for each event value
                            report_data_dict[TARGET_CN].append(current_target)
                            report_data_dict[GROUPS_CN].append(current_group_id)
                            report_data_dict[SOCKET_CN].append(current_socket_id)
                            report_data_dict[CORE_CN].append(current_core_id)
                            report_data_dict[EVENT_CN].append(current_event_id)
                            report_data_dict[EVENT_VALUE_CN].append(current_event_value)

        report = Report(data=report_data_dict)

        # We get the basic infos from the first entry of the list
        current_report_dict = reports_dict[0]
        metadata = {} if METADATA_CN not in current_report_dict.keys() else current_report_dict[METADATA_CN]
        return HWPCReportsGroup(timestamp=current_report_dict[TIMESTAMP_CN], sensor=current_report_dict[SENSOR_CN],
                                metadata=metadata, report=report)

    @staticmethod
    def is_information_in_reports_dict(reports_dict: [Dict[str, Any]]) -> bool:
        """ Check if information is present in the given list of dictionaries

            Required information is basic information from report and groups

            Args:
                reports_dict: List of dictionaries that contains information of the HWPC report

            Return:
                True if values are present, False otherwise
        """
        for current_report_dict in reports_dict:
            if not GROUPS_CN in current_report_dict.keys():
                return False
        return ReportsGroup.is_basic_information_in_reports_dict(reports_dict)

    def __repr__(self) -> str:
        return 'HWCPGroupsReport(timestamp: {timestamp}, sensor: {sensor}, targets: {targets},' \
               'metadata: {metadata}), report:{report}'.format(timestamp=self.timestamp, sensor=self.sensor,
                                                               targets=sorted(self.get_targets()),
                                                               metadata=str(self.metadata), report=self.report)

    # TODO Write a method for getting a event value by group, core and event name and target

    def get_event_value(self, target: str, group: str, socket: str, core: str, event_name: str):
        """ Search for a event value by using the given parameters

            Args:
                target: The target related to the event
                group: The group associated to the event
                socket: The socket associated to the event
                core: The core associated to the event
                event_name: Name of the event
            Return:
                The value of the event or None if it does not exist

        """
        event_value = None


        # We get the dictionary with (target,group,core,event_name) as key. Values are arrays with the indexes
        try:
            group_by_all_dict = self.report.groupby([TARGET_CN, GROUPS_CN, SOCKET_CN, CORE_CN, EVENT_CN],
                                                    sort=False).indices

            indices = group_by_all_dict[target, group, socket, core, event_name]  # This is an array
        except KeyError:
            indices = None

        if indices is not None:
            # There is only one index
            event_value = self.report.iloc[indices[0]][EVENT_VALUE_CN]

        return event_value

    def get_event_value_first_found_core(self, target: str, group: str, socket: str, event_name: str):
        """ Get the value for the event of the first found core in the report

            Args:
                target: The target related to the event
                group: The group related to the event
                socket: The socket related to the event
                event_name: The event name for retrieving the value
            Return:
                The value of the event or None if it does not exist
        """
        try:
            socket_index = self.report.groupby([TARGET_CN, GROUPS_CN, SOCKET_CN], sort=False).groups[target,group,socket][0]
            core = self.report.iloc[socket_index][CORE_CN]
        except KeyError:
            return None

        return self.get_event_value(target=target, group=group, socket=socket, event_name=event_name, core=core)



    def compute_event_average(self, target: str, group: str, socket: str, event_name: str):
        """ Compute the average for the given event

            Args:
                target: The target related to the event
                group: The group related to the event
                socket: The socket related to the event
                event_name: The event name
            Return:
                The average for the given event or None if it does not exist
        """
        event_average = None
        try:
            averages_dict = self.report.groupby([TARGET_CN, GROUPS_CN, SOCKET_CN, EVENT_CN], sort=False)[
                EVENT_VALUE_CN].mean()

            event_average = averages_dict[(target, group, socket, event_name)]
        except KeyError:
            pass

        return event_average

    def get_group_events(self, group: str):
        """ Returns a list with group events

            Return:
                list of group events. If the group does not exist, the list is empty
        """
        group_events = []
        group_events_keys = self.report.groupby([GROUPS_CN, EVENT_CN], sort=False).indices.keys()

        for group_events_key in group_events_keys:
            if group in group_events_key:
                group_events.append(group_events_key[1])  # group_event_key is a tuple (group_name,event_name)

        return group_events

    def compute_group_event_averages(self, group: str, target: str, socket: str):
        """ Compute the average of a group events

            Args:
                group: The group related to events
                target: The target related to events
                socket: The socket related to events
            Returns:
                The average of group events in a dictionary. If there is a problem with group, target and/or socket, None
                is returned

        """
        group_event_averages = None
        group_events = self.get_group_events(group)

        if len(group_events) > 0:
            group_event_averages = defaultdict(int)

            # We compute the average for all the events
            averages_dict = self.report.groupby([TARGET_CN, GROUPS_CN, SOCKET_CN, EVENT_CN], sort=False)[
                EVENT_VALUE_CN].mean()

            # We filter the group events average
            try:
                for event in group_events:
                    group_event_averages[event] = averages_dict[(target, group, socket, event)]
            except KeyError:
                group_event_averages = None

        return group_event_averages

    def compute_group_event_sum(self, group: str, target: str, socket: str):
        """ Compute the sum of a group events

            Args:
                group: The group related to events
                target: The target related to events
                socket: The socket related to events
            Returns:
                The sum of group events in a dictionary. If there is a problem with group, target and/or socket, None
                is returned

        """
        group_event_sum = None
        group_events = self.get_group_events(group)

        if len(group_events) > 0:
            group_event_sum = defaultdict(int)

            # We compute the sum for all the events
            sums_dict = self.report.groupby([TARGET_CN, GROUPS_CN, SOCKET_CN, EVENT_CN], sort=False)[
                EVENT_VALUE_CN].sum()

            # We filter the group events sum
            try:
                for event in group_events:
                    group_event_sum[event] = sums_dict[(target, group, socket, event)]
            except KeyError:
                group_event_sum = None

        return group_event_sum

    def compute_group_event_sum_excluding_target(self, group: str, target: str, socket: str):
        """ Compute the sum of a group events excluding the given target

            Args:
                group: The group related to events
                target: The target to be ignored in the sum
                socket: The socket related to events
            Returns:
                The sum of group events in a dictionary. If there is a problem with group and/or socket, None
                is returned

        """
        group_event_sum = None
        group_events = self.get_group_events(group)

        if len(group_events) > 0:
            group_event_sum = defaultdict(int)

            # We compute the sum for all the events
            sums_dict = self.report.groupby([TARGET_CN, GROUPS_CN, SOCKET_CN, EVENT_CN], sort=False)[
                EVENT_VALUE_CN].sum()
            # We filter the group events sum, and we exclude the given target
            try:
                for current_target in self.report.get_targets():
                    if current_target != target:
                        for event in group_events:

                                if event not in group_event_sum.keys():
                                    group_event_sum[event] = 0
                                group_event_sum[event] += sums_dict[(current_target, group, socket, event)]
            except KeyError:
                group_event_sum = None

        return group_event_sum


