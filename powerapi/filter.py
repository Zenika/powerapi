# Copyright (c) 2021, INRIA
# Copyright (c) 2021, University of Lille
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
from typing import Callable, List


from thespian.actors import ActorAddress

from powerapi.report import Report
from powerapi.exception import PowerAPIException


class RouterWithoutRuleException(PowerAPIException):
    """
    Exception raised when a filter route with 0 filters
    """
    def __init__(self):
        PowerAPIException.__init__(self, "")


class Filter:
    """
    Filter class

    A filter allow the Puller to route Report of the database to Dispatchers
    by fixing some rules.
    """

    def __init__(self):
        self.filters = []

    def filter(self, rule: Callable[[Report], bool], dispatcher: ActorAddress):
        """
        Define a rule for a kind of report, and send it to the dispatcher
        if the rule accept it.

        :param (func(report) -> bool) rule:      Function which return if
                                                 the report has to be send to
                                                 this dispatcher
        :param powerapi.Dispatcher dispatcher: Dispatcher we want to send the
                                                 report
        """
        self.filters.append((rule, dispatcher))

    def route(self, report: Report) -> List[ActorAddress]:
        """
        Get the list of dispatchers to whom send the report, or None

        :param powerapi.Report report: Message to send
        """
        if not self.filters:
            raise RuntimeError()

        dispatchers = []
        for rule, dispatcher in self.filters:
            if rule(report):
                dispatchers.append(dispatcher)

        return dispatchers
